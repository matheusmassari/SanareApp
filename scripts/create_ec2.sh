#!/bin/bash

# Script automatizado para criar EC2 SanareApp com melhores práticas de segurança
# SanareApp - Automated EC2 Setup

set -e  # Exit on any error

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configurações
PROJECT_NAME="SanareApp"
ENVIRONMENT="development"
KEY_NAME="sanare-dev-key"
SECURITY_GROUP_NAME="sanare-dev-sg"
INSTANCE_NAME="sanare-dev-server"
INSTANCE_TYPE="t3.micro"

# Funções auxiliares
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️ $1${NC}"
}

# Verificar pré-requisitos
check_prerequisites() {
    print_header "Verificando Pré-requisitos"
    
    # Verificar AWS CLI
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI não encontrado. Instale primeiro:"
        echo "https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
        exit 1
    fi
    print_success "AWS CLI encontrado"
    
    # Verificar configuração AWS
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS CLI não configurado. Execute: aws configure"
        exit 1
    fi
    print_success "AWS CLI configurado"
    
    # Verificar curl
    if ! command -v curl &> /dev/null; then
        print_error "curl não encontrado. Instale primeiro."
        exit 1
    fi
    print_success "curl encontrado"
    
    # Mostrar conta AWS atual
    ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    REGION=$(aws configure get region)
    print_info "Conta AWS: $ACCOUNT_ID"
    print_info "Região: $REGION"
}

# Obter IP público
get_public_ip() {
    print_header "Obtendo IP Público"
    
    PUBLIC_IP=$(curl -s https://ifconfig.me || curl -s https://ipinfo.io/ip || curl -s https://api.ipify.org)
    
    if [[ -z "$PUBLIC_IP" ]]; then
        print_error "Não foi possível obter seu IP público"
        exit 1
    fi
    
    print_success "Seu IP público: $PUBLIC_IP"
    echo "$PUBLIC_IP"
}

# Criar chave SSH
create_ssh_key() {
    print_header "Configurando Chave SSH"
    
    # Verificar se chave já existe
    if aws ec2 describe-key-pairs --key-names "$KEY_NAME" &> /dev/null; then
        print_warning "Chave SSH '$KEY_NAME' já existe"
        
        # Verificar se arquivo local existe
        if [[ ! -f ~/.ssh/${KEY_NAME}.pem ]]; then
            print_error "Chave existe na AWS mas arquivo local não encontrado"
            print_info "Delete a chave na AWS ou forneça o arquivo local"
            exit 1
        fi
        
        print_success "Usando chave SSH existente"
        return 0
    fi
    
    # Criar nova chave
    print_info "Criando nova chave SSH: $KEY_NAME"
    
    aws ec2 create-key-pair \
        --key-name "$KEY_NAME" \
        --query 'KeyMaterial' \
        --output text > ~/.ssh/${KEY_NAME}.pem
    
    # Configurar permissões
    chmod 400 ~/.ssh/${KEY_NAME}.pem
    
    print_success "Chave SSH criada: ~/.ssh/${KEY_NAME}.pem"
    
    # Backup da chave
    BACKUP_DIR="$HOME/Documents/AWS_Keys"
    mkdir -p "$BACKUP_DIR"
    cp ~/.ssh/${KEY_NAME}.pem "$BACKUP_DIR/${KEY_NAME}.pem.backup"
    print_success "Backup da chave criado em: $BACKUP_DIR"
}

# Criar Security Group
create_security_group() {
    print_header "Configurando Security Group"
    
    # Verificar se Security Group já existe
    if aws ec2 describe-security-groups --group-names "$SECURITY_GROUP_NAME" &> /dev/null; then
        print_warning "Security Group '$SECURITY_GROUP_NAME' já existe"
        SECURITY_GROUP_ID=$(aws ec2 describe-security-groups \
            --group-names "$SECURITY_GROUP_NAME" \
            --query 'SecurityGroups[0].GroupId' \
            --output text)
        print_success "Usando Security Group existente: $SECURITY_GROUP_ID"
        echo "$SECURITY_GROUP_ID"
        return 0
    fi
    
    # Criar Security Group
    print_info "Criando Security Group: $SECURITY_GROUP_NAME"
    
    SECURITY_GROUP_ID=$(aws ec2 create-security-group \
        --group-name "$SECURITY_GROUP_NAME" \
        --description "Security Group para ambiente de desenvolvimento $PROJECT_NAME" \
        --tag-specifications "ResourceType=security-group,Tags=[{Key=Name,Value=$SECURITY_GROUP_NAME},{Key=Environment,Value=$ENVIRONMENT},{Key=Project,Value=$PROJECT_NAME}]" \
        --query 'GroupId' \
        --output text)
    
    print_success "Security Group criado: $SECURITY_GROUP_ID"
    
    # Configurar regras de entrada
    print_info "Configurando regras de segurança..."
    
    # SSH apenas do seu IP
    aws ec2 authorize-security-group-ingress \
        --group-id "$SECURITY_GROUP_ID" \
        --protocol tcp \
        --port 22 \
        --cidr "${PUBLIC_IP}/32" \
        --tag-specifications "ResourceType=security-group-rule,Tags=[{Key=Name,Value=SSH-Access}]"
    print_success "Regra SSH configurada"
    
    # FastAPI para desenvolvimento
    aws ec2 authorize-security-group-ingress \
        --group-id "$SECURITY_GROUP_ID" \
        --protocol tcp \
        --port 8000 \
        --cidr "${PUBLIC_IP}/32" \
        --tag-specifications "ResourceType=security-group-rule,Tags=[{Key=Name,Value=FastAPI-Dev}]"
    print_success "Regra FastAPI configurada"
    
    # PostgreSQL apenas do seu IP
    aws ec2 authorize-security-group-ingress \
        --group-id "$SECURITY_GROUP_ID" \
        --protocol tcp \
        --port 5432 \
        --cidr "${PUBLIC_IP}/32" \
        --tag-specifications "ResourceType=security-group-rule,Tags=[{Key=Name,Value=PostgreSQL-Access}]"
    print_success "Regra PostgreSQL configurada"
    
    # HTTPS para futuro
    aws ec2 authorize-security-group-ingress \
        --group-id "$SECURITY_GROUP_ID" \
        --protocol tcp \
        --port 443 \
        --cidr "0.0.0.0/0" \
        --tag-specifications "ResourceType=security-group-rule,Tags=[{Key=Name,Value=HTTPS-Public}]"
    print_success "Regra HTTPS configurada"
    
    echo "$SECURITY_GROUP_ID"
}

# Criar script de inicialização
create_user_data() {
    print_header "Criando Script de Inicialização"
    
    cat > user-data.sh << EOF
#!/bin/bash

# Log de início
echo "\$(date): Iniciando bootstrap da instância" >> /var/log/user-data.log

# Atualizar sistema
apt-get update -y >> /var/log/user-data.log 2>&1
apt-get upgrade -y >> /var/log/user-data.log 2>&1

# Instalar pacotes essenciais
apt-get install -y \\
    curl \\
    wget \\
    git \\
    htop \\
    unzip \\
    software-properties-common \\
    apt-transport-https \\
    ca-certificates \\
    gnupg \\
    lsb-release >> /var/log/user-data.log 2>&1

# Configurar timezone
timedatectl set-timezone America/Sao_Paulo >> /var/log/user-data.log 2>&1

# Instalar Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \$(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

apt-get update -y >> /var/log/user-data.log 2>&1
apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin >> /var/log/user-data.log 2>&1

# Adicionar usuário ubuntu ao grupo docker
usermod -aG docker ubuntu

# Habilitar Docker
systemctl enable docker >> /var/log/user-data.log 2>&1
systemctl start docker >> /var/log/user-data.log 2>&1

# Instalar Docker Compose standalone
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-\$(uname -s)-\$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Configurar firewall
ufw --force enable >> /var/log/user-data.log 2>&1
ufw default deny incoming >> /var/log/user-data.log 2>&1
ufw default allow outgoing >> /var/log/user-data.log 2>&1
ufw allow ssh >> /var/log/user-data.log 2>&1
ufw allow from ${PUBLIC_IP} to any port 8000 >> /var/log/user-data.log 2>&1
ufw allow from ${PUBLIC_IP} to any port 5432 >> /var/log/user-data.log 2>&1

# Criar estrutura de diretórios
mkdir -p /home/ubuntu/sanare-app >> /var/log/user-data.log 2>&1
chown ubuntu:ubuntu /home/ubuntu/sanare-app

# Configurar Docker para iniciar automaticamente
systemctl enable docker.service >> /var/log/user-data.log 2>&1
systemctl enable containerd.service >> /var/log/user-data.log 2>&1

# Log de conclusão
echo "\$(date): Bootstrap concluído com sucesso" >> /var/log/user-data.log

EOF
    
    print_success "Script de inicialização criado"
}

# Obter AMI do Ubuntu
get_ubuntu_ami() {
    print_header "Obtendo AMI do Ubuntu"
    
    AMI_ID=$(aws ec2 describe-images \
        --owners 099720109477 \
        --filters "Name=name,Values=ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*" \
        --query 'Images | sort_by(@, &CreationDate) | [-1].ImageId' \
        --output text)
    
    if [[ -z "$AMI_ID" ]]; then
        print_error "Não foi possível encontrar AMI do Ubuntu"
        exit 1
    fi
    
    print_success "AMI Ubuntu encontrada: $AMI_ID"
    echo "$AMI_ID"
}

# Criar instância EC2
create_instance() {
    print_header "Criando Instância EC2"
    
    # Verificar se instância já existe
    EXISTING_INSTANCE=$(aws ec2 describe-instances \
        --filters "Name=tag:Name,Values=$INSTANCE_NAME" "Name=instance-state-name,Values=running,pending,stopping,stopped" \
        --query 'Reservations[0].Instances[0].InstanceId' \
        --output text 2>/dev/null || echo "None")
    
    if [[ "$EXISTING_INSTANCE" != "None" ]]; then
        print_warning "Instância '$INSTANCE_NAME' já existe: $EXISTING_INSTANCE"
        
        STATE=$(aws ec2 describe-instances \
            --instance-ids "$EXISTING_INSTANCE" \
            --query 'Reservations[0].Instances[0].State.Name' \
            --output text)
        
        print_info "Estado atual: $STATE"
        
        if [[ "$STATE" == "stopped" ]]; then
            print_info "Iniciando instância existente..."
            aws ec2 start-instances --instance-ids "$EXISTING_INSTANCE"
            aws ec2 wait instance-running --instance-ids "$EXISTING_INSTANCE"
        fi
        
        echo "$EXISTING_INSTANCE"
        return 0
    fi
    
    print_info "Criando nova instância: $INSTANCE_NAME"
    
    INSTANCE_ID=$(aws ec2 run-instances \
        --image-id "$AMI_ID" \
        --count 1 \
        --instance-type "$INSTANCE_TYPE" \
        --key-name "$KEY_NAME" \
        --security-group-ids "$SECURITY_GROUP_ID" \
        --user-data file://user-data.sh \
        --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$INSTANCE_NAME},{Key=Environment,Value=$ENVIRONMENT},{Key=Project,Value=$PROJECT_NAME},{Key=AutoStop,Value=true}]" \
        --monitoring Enabled=true \
        --metadata-options HttpTokens=required,HttpPutResponseHopLimit=1,HttpEndpoint=enabled \
        --query 'Instances[0].InstanceId' \
        --output text)
    
    if [[ -z "$INSTANCE_ID" ]]; then
        print_error "Falha ao criar instância"
        exit 1
    fi
    
    print_success "Instância criada: $INSTANCE_ID"
    
    # Aguardar instância ficar disponível
    print_info "Aguardando instância ficar disponível..."
    aws ec2 wait instance-running --instance-ids "$INSTANCE_ID"
    
    print_success "Instância está rodando!"
    echo "$INSTANCE_ID"
}

# Obter informações da instância
get_instance_info() {
    local instance_id=$1
    
    INSTANCE_PUBLIC_IP=$(aws ec2 describe-instances \
        --instance-ids "$instance_id" \
        --query 'Reservations[0].Instances[0].PublicIpAddress' \
        --output text)
    
    INSTANCE_PRIVATE_IP=$(aws ec2 describe-instances \
        --instance-ids "$instance_id" \
        --query 'Reservations[0].Instances[0].PrivateIpAddress' \
        --output text)
    
    print_success "IP Público: $INSTANCE_PUBLIC_IP"
    print_success "IP Privado: $INSTANCE_PRIVATE_IP"
}

# Configurar monitoramento
setup_monitoring() {
    local instance_id=$1
    
    print_header "Configurando Monitoramento"
    
    # Habilitar monitoramento detalhado
    aws ec2 monitor-instances --instance-ids "$instance_id"
    print_success "Monitoramento detalhado habilitado"
    
    # Criar alarme de CPU
    aws cloudwatch put-metric-alarm \
        --alarm-name "${PROJECT_NAME}-dev-high-cpu" \
        --alarm-description "Alarme para CPU alta na instância de desenvolvimento" \
        --metric-name CPUUtilization \
        --namespace AWS/EC2 \
        --statistic Average \
        --period 300 \
        --threshold 80 \
        --comparison-operator GreaterThanThreshold \
        --dimensions Name=InstanceId,Value="$instance_id" \
        --evaluation-periods 2 \
        --tags Key=Project,Value="$PROJECT_NAME"
    
    print_success "Alarme de CPU configurado"
}

# Criar scripts de gerenciamento
create_management_scripts() {
    local instance_id=$1
    local instance_ip=$2
    
    print_header "Criando Scripts de Gerenciamento"
    
    # Script de gerenciamento
    cat > manage_ec2.sh << EOF
#!/bin/bash

INSTANCE_ID="$instance_id"
KEY_PATH="~/.ssh/${KEY_NAME}.pem"

case \$1 in
  start)
    echo "Iniciando instância..."
    aws ec2 start-instances --instance-ids \$INSTANCE_ID
    aws ec2 wait instance-running --instance-ids \$INSTANCE_ID
    PUBLIC_IP=\$(aws ec2 describe-instances --instance-ids \$INSTANCE_ID --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)
    echo "✅ Instância disponível em: \$PUBLIC_IP"
    ;;
  stop)
    echo "Parando instância..."
    aws ec2 stop-instances --instance-ids \$INSTANCE_ID
    echo "✅ Comando de parada enviado"
    ;;
  status)
    aws ec2 describe-instances --instance-ids \$INSTANCE_ID --query 'Reservations[0].Instances[0].[State.Name,PublicIpAddress,PrivateIpAddress]' --output table
    ;;
  ssh)
    PUBLIC_IP=\$(aws ec2 describe-instances --instance-ids \$INSTANCE_ID --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)
    ssh -i \$KEY_PATH ubuntu@\$PUBLIC_IP
    ;;
  info)
    echo "Instance ID: \$INSTANCE_ID"
    echo "Key Path: \$KEY_PATH"
    echo "Security Group: $SECURITY_GROUP_ID"
    ;;
  *)
    echo "Uso: \$0 {start|stop|status|ssh|info}"
    ;;
esac
EOF
    
    chmod +x manage_ec2.sh
    print_success "Script de gerenciamento criado: manage_ec2.sh"
    
    # Salvar informações
    cat > ec2_info.txt << EOF
# Informações da Instância EC2 - $PROJECT_NAME

Instance ID: $instance_id
Public IP: $instance_ip
Security Group ID: $SECURITY_GROUP_ID
Key Name: $KEY_NAME
Key Path: ~/.ssh/${KEY_NAME}.pem
Region: $(aws configure get region)
Created: $(date)

# Comandos úteis:
# Conectar: ssh -i ~/.ssh/${KEY_NAME}.pem ubuntu@$instance_ip
# Gerenciar: ./manage_ec2.sh {start|stop|status|ssh|info}
EOF
    
    print_success "Informações salvas em: ec2_info.txt"
}

# Função principal
main() {
    print_header "SanareApp - Configuração Automática da EC2"
    
    # Verificar pré-requisitos
    check_prerequisites
    
    # Obter IP público
    PUBLIC_IP=$(get_public_ip)
    
    # Criar chave SSH
    create_ssh_key
    
    # Criar Security Group
    SECURITY_GROUP_ID=$(create_security_group)
    
    # Criar script de inicialização
    create_user_data
    
    # Obter AMI do Ubuntu
    AMI_ID=$(get_ubuntu_ami)
    
    # Criar instância
    INSTANCE_ID=$(create_instance)
    
    # Obter informações da instância
    get_instance_info "$INSTANCE_ID"
    
    # Configurar monitoramento
    setup_monitoring "$INSTANCE_ID"
    
    # Criar scripts de gerenciamento
    create_management_scripts "$INSTANCE_ID" "$INSTANCE_PUBLIC_IP"
    
    # Sucesso final
    print_header "Configuração Concluída com Sucesso!"
    
    echo -e "${GREEN}✅ Instância EC2 criada e configurada${NC}"
    echo -e "${GREEN}✅ Instance ID: $INSTANCE_ID${NC}"
    echo -e "${GREEN}✅ IP Público: $INSTANCE_PUBLIC_IP${NC}"
    echo -e "${GREEN}✅ Chave SSH: ~/.ssh/${KEY_NAME}.pem${NC}"
    
    print_warning "Aguarde 2-3 minutos para o bootstrap completar"
    print_info "Teste a conexão: ssh -i ~/.ssh/${KEY_NAME}.pem ubuntu@$INSTANCE_PUBLIC_IP"
    print_info "Gerencie a instância: ./manage_ec2.sh {start|stop|status|ssh}"
    
    # Cleanup
    rm -f user-data.sh
}

# Executar função principal
main "$@" 