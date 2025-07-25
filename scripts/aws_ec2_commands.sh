#!/bin/bash
# 
# Script com comandos úteis para gerenciar EC2 com PostgreSQL
# SanareApp - AWS EC2 Management
#

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configurações (CUSTOMIZE AQUI)
INSTANCE_ID=""  # Preencher após criar a instância
KEY_NAME=""     # Nome da sua chave SSH
KEY_PATH=""     # Caminho para o arquivo .pem
EC2_USER="ubuntu"

# Funções auxiliares
print_header() {
    echo -e "${BLUE}======================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}======================================${NC}"
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

# Verificar se AWS CLI está configurado
check_aws_cli() {
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI não encontrado. Instale primeiro:"
        echo "https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
        exit 1
    fi
    
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS CLI não configurado. Execute: aws configure"
        exit 1
    fi
    
    print_success "AWS CLI configurado"
}

# Obter informações da instância
get_instance_info() {
    if [[ -z "$INSTANCE_ID" ]]; then
        print_error "INSTANCE_ID não configurado no script"
        exit 1
    fi
    
    echo "Instance ID: $INSTANCE_ID"
    aws ec2 describe-instances --instance-ids "$INSTANCE_ID" --query 'Reservations[0].Instances[0].[State.Name,PublicIpAddress,PrivateIpAddress]' --output table
}

# Obter IP público da instância
get_public_ip() {
    aws ec2 describe-instances --instance-ids "$INSTANCE_ID" --query 'Reservations[0].Instances[0].PublicIpAddress' --output text
}

# Iniciar instância
start_instance() {
    print_header "Iniciando instância EC2"
    
    aws ec2 start-instances --instance-ids "$INSTANCE_ID"
    
    if [[ $? -eq 0 ]]; then
        print_success "Comando de start enviado"
        print_warning "Aguarde alguns minutos para a instância ficar disponível"
        
        echo "Aguardando instância ficar disponível..."
        aws ec2 wait instance-running --instance-ids "$INSTANCE_ID"
        
        PUBLIC_IP=$(get_public_ip)
        print_success "Instância disponível em: $PUBLIC_IP"
    else
        print_error "Falha ao iniciar instância"
    fi
}

# Parar instância
stop_instance() {
    print_header "Parando instância EC2"
    
    aws ec2 stop-instances --instance-ids "$INSTANCE_ID"
    
    if [[ $? -eq 0 ]]; then
        print_success "Comando de stop enviado"
        print_warning "Aguarde alguns minutos para a instância parar completamente"
    else
        print_error "Falha ao parar instância"
    fi
}

# Conectar via SSH
ssh_connect() {
    print_header "Conectando via SSH"
    
    if [[ -z "$KEY_PATH" ]]; then
        print_error "KEY_PATH não configurado"
        exit 1
    fi
    
    PUBLIC_IP=$(get_public_ip)
    
    if [[ "$PUBLIC_IP" == "None" ]] || [[ -z "$PUBLIC_IP" ]]; then
        print_error "Instância não tem IP público. Está rodando?"
        exit 1
    fi
    
    echo "Conectando em: $EC2_USER@$PUBLIC_IP"
    ssh -i "$KEY_PATH" "$EC2_USER@$PUBLIC_IP"
}

# Verificar status do PostgreSQL
check_postgres() {
    print_header "Verificando PostgreSQL na EC2"
    
    PUBLIC_IP=$(get_public_ip)
    
    if [[ "$PUBLIC_IP" == "None" ]] || [[ -z "$PUBLIC_IP" ]]; then
        print_error "Instância não tem IP público"
        exit 1
    fi
    
    echo "Verificando PostgreSQL em: $PUBLIC_IP"
    
    ssh -i "$KEY_PATH" "$EC2_USER@$PUBLIC_IP" << 'EOF'
echo "🔍 Status do PostgreSQL:"
sudo systemctl status postgresql --no-pager

echo -e "\n🔥 Firewall status:"
sudo ufw status

echo -e "\n📊 Conexões ativas:"
sudo -u postgres psql -c "SELECT count(*) as active_connections FROM pg_stat_activity;"

echo -e "\n💾 Uso de disco:"
df -h /var/lib/postgresql/
EOF
}

# Fazer backup do banco
backup_database() {
    print_header "Fazendo backup do banco"
    
    PUBLIC_IP=$(get_public_ip)
    BACKUP_NAME="sanare_db_backup_$(date +%Y%m%d_%H%M%S).sql"
    
    echo "Fazendo backup para: $BACKUP_NAME"
    
    ssh -i "$KEY_PATH" "$EC2_USER@$PUBLIC_IP" << EOF
echo "📦 Criando backup..."
sudo -u postgres pg_dump sanare_db > /tmp/$BACKUP_NAME
echo "✅ Backup criado: /tmp/$BACKUP_NAME"

echo "📊 Tamanho do backup:"
ls -lh /tmp/$BACKUP_NAME
EOF
    
    # Download backup
    echo "💾 Baixando backup..."
    scp -i "$KEY_PATH" "$EC2_USER@$PUBLIC_IP:/tmp/$BACKUP_NAME" "./backups/"
    
    if [[ $? -eq 0 ]]; then
        print_success "Backup baixado para: ./backups/$BACKUP_NAME"
    else
        print_error "Falha ao baixar backup"
    fi
}

# Atualizar Security Group com novo IP
update_security_group() {
    print_header "Atualizando Security Group"
    
    # Obter IP atual
    CURRENT_IP=$(curl -s https://ifconfig.me)
    echo "Seu IP atual: $CURRENT_IP"
    
    # Você precisará do Group ID do seu Security Group
    SECURITY_GROUP_ID=""  # Preencher com o ID do seu Security Group
    
    if [[ -z "$SECURITY_GROUP_ID" ]]; then
        print_error "SECURITY_GROUP_ID não configurado"
        echo "Use: aws ec2 describe-security-groups --group-names sanare-postgres-sg"
        exit 1
    fi
    
    # Remover regras antigas (opcional)
    echo "⚠️ Removendo regras antigas (se existirem)..."
    
    # Adicionar nova regra
    echo "➕ Adicionando nova regra para IP: $CURRENT_IP"
    
    aws ec2 authorize-security-group-ingress \
        --group-id "$SECURITY_GROUP_ID" \
        --protocol tcp \
        --port 5432 \
        --cidr "$CURRENT_IP/32" \
        --rule-description "SanareApp PostgreSQL access"
    
    if [[ $? -eq 0 ]]; then
        print_success "Security Group atualizado"
    else
        print_warning "Regra pode já existir ou houve erro"
    fi
}

# Monitorar logs do PostgreSQL
monitor_logs() {
    print_header "Monitorando logs do PostgreSQL"
    
    PUBLIC_IP=$(get_public_ip)
    
    ssh -i "$KEY_PATH" "$EC2_USER@$PUBLIC_IP" << 'EOF'
echo "📋 Últimas 50 linhas do log:"
sudo tail -n 50 /var/log/postgresql/postgresql-*-main.log

echo -e "\n👀 Monitorando logs em tempo real (Ctrl+C para sair):"
sudo tail -f /var/log/postgresql/postgresql-*-main.log
EOF
}

# Criar snapshot do volume EBS
create_snapshot() {
    print_header "Criando snapshot do volume EBS"
    
    # Obter volume ID
    VOLUME_ID=$(aws ec2 describe-instances --instance-ids "$INSTANCE_ID" --query 'Reservations[0].Instances[0].BlockDeviceMappings[0].Ebs.VolumeId' --output text)
    
    echo "Volume ID: $VOLUME_ID"
    
    DESCRIPTION="SanareApp PostgreSQL backup $(date)"
    
    aws ec2 create-snapshot \
        --volume-id "$VOLUME_ID" \
        --description "$DESCRIPTION"
    
    if [[ $? -eq 0 ]]; then
        print_success "Snapshot criado"
    else
        print_error "Falha ao criar snapshot"
    fi
}

# Menu principal
show_menu() {
    print_header "SanareApp - AWS EC2 Manager"
    echo "1. Verificar status da instância"
    echo "2. Iniciar instância"
    echo "3. Parar instância"
    echo "4. Conectar via SSH"
    echo "5. Verificar PostgreSQL"
    echo "6. Fazer backup do banco"
    echo "7. Atualizar Security Group"
    echo "8. Monitorar logs"
    echo "9. Criar snapshot EBS"
    echo "0. Sair"
    echo -e "${BLUE}======================================${NC}"
}

# Função principal
main() {
    check_aws_cli
    
    if [[ $# -eq 0 ]]; then
        while true; do
            show_menu
            read -p "Escolha uma opção: " choice
            
            case $choice in
                1) get_instance_info ;;
                2) start_instance ;;
                3) stop_instance ;;
                4) ssh_connect ;;
                5) check_postgres ;;
                6) backup_database ;;
                7) update_security_group ;;
                8) monitor_logs ;;
                9) create_snapshot ;;
                0) exit 0 ;;
                *) print_error "Opção inválida" ;;
            esac
            
            echo ""
            read -p "Pressione Enter para continuar..."
        done
    else
        # Comandos diretos
        case $1 in
            start) start_instance ;;
            stop) stop_instance ;;
            status) get_instance_info ;;
            ssh) ssh_connect ;;
            postgres) check_postgres ;;
            backup) backup_database ;;
            logs) monitor_logs ;;
            snapshot) create_snapshot ;;
            *) echo "Comandos: start, stop, status, ssh, postgres, backup, logs, snapshot" ;;
        esac
    fi
}

# Criar diretório de backups se não existir
mkdir -p backups

# Executar função principal
main "$@" 