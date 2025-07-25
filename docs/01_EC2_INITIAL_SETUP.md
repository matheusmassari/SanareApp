# Passo 1: Configuração Inicial da EC2 - SanareApp

Este guia vai te ajudar a criar uma instância EC2 no tier gratuito seguindo as melhores práticas de segurança para ambientes de desenvolvimento e produção.

## 🎯 **Objetivo desta Etapa**

Criar uma EC2 t3.micro (tier gratuito) com:
- ✅ Configuração de segurança robusta
- ✅ Chaves SSH adequadas
- ✅ Security Groups restritivos
- ✅ Monitoramento básico
- ✅ Backup automático

## 📋 **Pré-requisitos**

- [ ] Conta AWS ativa
- [ ] AWS CLI instalado
- [ ] Conhecimento do seu IP público atual

## 🚀 **Passo 1.1: Verificar e Configurar AWS CLI**

### **Instalar AWS CLI (se necessário)**

```bash
# macOS
brew install awscli

# Verificar instalação
aws --version
```

### **Configurar AWS CLI**

```bash
# Configurar credenciais
aws configure

# Você precisará de:
# - AWS Access Key ID
# - AWS Secret Access Key  
# - Default region: us-east-1 (ou sua preferência)
# - Default output format: json
```

### **Testar configuração**

```bash
# Verificar identidade
aws sts get-caller-identity

# Verificar regiões disponíveis
aws ec2 describe-regions --output table
```

## 🔐 **Passo 1.2: Criar Chave SSH**

### **Criar novo par de chaves**

```bash
# Criar chave SSH específica para SanareApp
aws ec2 create-key-pair \
  --key-name sanare-dev-key \
  --query 'KeyMaterial' \
  --output text > ~/.ssh/sanare-dev-key.pem

# Definir permissões corretas
chmod 400 ~/.ssh/sanare-dev-key.pem

# Verificar chave criada
aws ec2 describe-key-pairs --key-names sanare-dev-key
```

### **Backup da chave (IMPORTANTE)**

```bash
# Fazer backup da chave em local seguro
cp ~/.ssh/sanare-dev-key.pem ~/Documents/AWS_Keys/sanare-dev-key.pem.backup

# ⚠️ NUNCA commite esta chave no Git!
```

## 🛡️ **Passo 1.3: Configurar Security Groups**

### **Obter seu IP público atual**

```bash
# Descobrir seu IP público
curl -s https://ifconfig.me
# Anote este IP - você precisará dele
```

### **Criar Security Group para desenvolvimento**

```bash
# Criar Security Group
aws ec2 create-security-group \
  --group-name sanare-dev-sg \
  --description "Security Group para ambiente de desenvolvimento SanareApp" \
  --tag-specifications 'ResourceType=security-group,Tags=[{Key=Name,Value=sanare-dev-sg},{Key=Environment,Value=development},{Key=Project,Value=SanareApp}]'

# Anote o GroupId retornado
```

### **Configurar regras de entrada (substitua SEU_IP)**

```bash
# Obter o Group ID
SECURITY_GROUP_ID=$(aws ec2 describe-security-groups \
  --group-names sanare-dev-sg \
  --query 'SecurityGroups[0].GroupId' \
  --output text)

echo "Security Group ID: $SECURITY_GROUP_ID"

# SSH apenas do seu IP
aws ec2 authorize-security-group-ingress \
  --group-id $SECURITY_GROUP_ID \
  --protocol tcp \
  --port 22 \
  --cidr SEU_IP_AQUI/32 \
  --tag-specifications 'ResourceType=security-group-rule,Tags=[{Key=Name,Value=SSH-Access}]'

# HTTP para aplicação (temporário para desenvolvimento)
aws ec2 authorize-security-group-ingress \
  --group-id $SECURITY_GROUP_ID \
  --protocol tcp \
  --port 8000 \
  --cidr SEU_IP_AQUI/32 \
  --tag-specifications 'ResourceType=security-group-rule,Tags=[{Key=Name,Value=FastAPI-Dev}]'

# PostgreSQL apenas do seu IP
aws ec2 authorize-security-group-ingress \
  --group-id $SECURITY_GROUP_ID \
  --protocol tcp \
  --port 5432 \
  --cidr SEU_IP_AQUI/32 \
  --tag-specifications 'ResourceType=security-group-rule,Tags=[{Key=Name,Value=PostgreSQL-Access}]'

# HTTPS (para futuro)
aws ec2 authorize-security-group-ingress \
  --group-id $SECURITY_GROUP_ID \
  --protocol tcp \
  --port 443 \
  --cidr 0.0.0.0/0 \
  --tag-specifications 'ResourceType=security-group-rule,Tags=[{Key=Name,Value=HTTPS-Public}]'
```

### **Verificar Security Group configurado**

```bash
# Verificar regras criadas
aws ec2 describe-security-groups \
  --group-ids $SECURITY_GROUP_ID \
  --output table
```

## 🖥️ **Passo 1.4: Criar Instância EC2**

### **Encontrar AMI do Ubuntu mais recente**

```bash
# Buscar AMI do Ubuntu 24.04 LTS
aws ec2 describe-images \
  --owners 099720109477 \
  --filters "Name=name,Values=ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*" \
  --query 'Images | sort_by(@, &CreationDate) | [-1].ImageId' \
  --output text
```

### **Criar script de inicialização (User Data)**

```bash
# Criar script de bootstrap
cat > user-data.sh << 'EOF'
#!/bin/bash

# Atualizar sistema
apt-get update -y
apt-get upgrade -y

# Instalar pacotes essenciais
apt-get install -y \
  curl \
  wget \
  git \
  htop \
  unzip \
  software-properties-common \
  apt-transport-https \
  ca-certificates \
  gnupg \
  lsb-release

# Configurar timezone
timedatectl set-timezone America/Sao_Paulo

# Instalar Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

apt-get update -y
apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Adicionar usuário ubuntu ao grupo docker
usermod -aG docker ubuntu

# Habilitar Docker
systemctl enable docker
systemctl start docker

# Instalar Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Configurar firewall
ufw --force enable
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow from SEU_IP_AQUI to any port 8000
ufw allow from SEU_IP_AQUI to any port 5432

# Criar estrutura de diretórios
mkdir -p /home/ubuntu/sanare-app
chown ubuntu:ubuntu /home/ubuntu/sanare-app

# Log de conclusão
echo "$(date): Bootstrap concluído" >> /var/log/user-data.log

EOF

# Substituir SEU_IP_AQUI pelo seu IP real no arquivo
sed -i 's/SEU_IP_AQUI/SEU_IP_REAL/g' user-data.sh
```

### **Lançar a instância**

```bash
# Obter AMI ID
AMI_ID=$(aws ec2 describe-images \
  --owners 099720109477 \
  --filters "Name=name,Values=ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*" \
  --query 'Images | sort_by(@, &CreationDate) | [-1].ImageId' \
  --output text)

echo "AMI ID: $AMI_ID"

# Lançar instância
aws ec2 run-instances \
  --image-id $AMI_ID \
  --count 1 \
  --instance-type t3.micro \
  --key-name sanare-dev-key \
  --security-group-ids $SECURITY_GROUP_ID \
  --user-data file://user-data.sh \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=sanare-dev-server},{Key=Environment,Value=development},{Key=Project,Value=SanareApp},{Key=Owner,Value=SeuNome}]' \
  --monitoring Enabled=true \
  --metadata-options HttpTokens=required,HttpPutResponseHopLimit=1,HttpEndpoint=enabled
```

### **Aguardar instância ficar disponível**

```bash
# Obter Instance ID
INSTANCE_ID=$(aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=sanare-dev-server" "Name=instance-state-name,Values=running,pending" \
  --query 'Reservations[0].Instances[0].InstanceId' \
  --output text)

echo "Instance ID: $INSTANCE_ID"

# Aguardar instância ficar em execução
echo "Aguardando instância ficar disponível..."
aws ec2 wait instance-running --instance-ids $INSTANCE_ID

# Obter IP público
PUBLIC_IP=$(aws ec2 describe-instances \
  --instance-ids $INSTANCE_ID \
  --query 'Reservations[0].Instances[0].PublicIpAddress' \
  --output text)

echo "✅ Instância criada com sucesso!"
echo "📍 IP Público: $PUBLIC_IP"
echo "🔑 Chave SSH: ~/.ssh/sanare-dev-key.pem"
```

## 🔍 **Passo 1.5: Verificar Configuração**

### **Testar conexão SSH**

```bash
# Aguardar alguns minutos para o bootstrap completar
echo "Aguardando 3 minutos para completar inicialização..."
sleep 180

# Conectar via SSH
ssh -i ~/.ssh/sanare-dev-key.pem ubuntu@$PUBLIC_IP

# Dentro da instância, verificar:
# - Docker: docker --version
# - Docker Compose: docker-compose --version
# - Firewall: sudo ufw status
# - Logs de bootstrap: sudo tail -f /var/log/user-data.log
```

### **Verificar serviços instalados**

```bash
# Via SSH na instância, executar:
echo "=== Verificação dos Serviços ==="

echo "✅ Docker Version:"
docker --version

echo -e "\n✅ Docker Compose Version:"
docker-compose --version

echo -e "\n✅ Docker Status:"
sudo systemctl status docker --no-pager

echo -e "\n✅ Firewall Status:"
sudo ufw status

echo -e "\n✅ Disk Usage:"
df -h

echo -e "\n✅ Memory Usage:"
free -h

echo -e "\n✅ Bootstrap Log:"
tail -10 /var/log/user-data.log
```

## 📊 **Passo 1.6: Configurar Monitoramento Básico**

### **Habilitar CloudWatch detalhado**

```bash
# Habilitar monitoramento detalhado
aws ec2 monitor-instances --instance-ids $INSTANCE_ID

# Criar alarme para CPU alta
aws cloudwatch put-metric-alarm \
  --alarm-name "sanare-dev-high-cpu" \
  --alarm-description "Alarme para CPU alta na instância de desenvolvimento" \
  --metric-name CPUUtilization \
  --namespace AWS/EC2 \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=InstanceId,Value=$INSTANCE_ID \
  --evaluation-periods 2
```

## 💰 **Passo 1.7: Configurar Economia de Custos**

### **Script para stop/start automático**

```bash
# Criar script local para gerenciar a instância
cat > manage_ec2.sh << EOF
#!/bin/bash

INSTANCE_ID="$INSTANCE_ID"

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
    echo "✅ Instância parada"
    ;;
  status)
    aws ec2 describe-instances --instance-ids \$INSTANCE_ID --query 'Reservations[0].Instances[0].[State.Name,PublicIpAddress]' --output table
    ;;
  ssh)
    PUBLIC_IP=\$(aws ec2 describe-instances --instance-ids \$INSTANCE_ID --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)
    ssh -i ~/.ssh/sanare-dev-key.pem ubuntu@\$PUBLIC_IP
    ;;
  *)
    echo "Uso: \$0 {start|stop|status|ssh}"
    ;;
esac
EOF

chmod +x manage_ec2.sh
```

## ✅ **Checklist de Verificação**

Antes de prosseguir para o próximo passo, verifique:

- [ ] EC2 criada e rodando
- [ ] SSH funcionando com chave privada
- [ ] Docker instalado e funcionando
- [ ] Docker Compose instalado
- [ ] Firewall configurado (ufw)
- [ ] Security Group com regras restritivas
- [ ] Monitoramento básico configurado
- [ ] Scripts de gerenciamento criados

## 📝 **Informações para Próximos Passos**

Anote estas informações para usar nos próximos passos:

```bash
# Salvar informações importantes
cat > ec2_info.txt << EOF
Instance ID: $INSTANCE_ID
Public IP: $PUBLIC_IP
Security Group ID: $SECURITY_GROUP_ID
Key Path: ~/.ssh/sanare-dev-key.pem
Region: $(aws configure get region)
EOF

echo "✅ Informações salvas em ec2_info.txt"
```

## 🎯 **Próximo Passo**

Com a EC2 criada e configurada, o próximo passo será:
- **Passo 2**: Configurar ambiente Docker para desenvolvimento e produção

---

**🎉 Parabéns! Você configurou uma EC2 segura seguindo as melhores práticas!** 