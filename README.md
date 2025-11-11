# Projeto IoT – Viveiro de Eucalipto  
### *Streaming de dados em tempo real com Kafka, Spark e Postgres*

## Contexto do Projeto

Viveiros de eucalipto são essenciais para abastecer fábricas de celulose na produção de papel. Esses viveiros abrigam **milhares de clones de eucalipto** e dependem de um controle ambiental rigoroso para garantir o desenvolvimento saudável das mudas.

Para manter as plantas de forma autônoma, os viveiros modernos utilizam **centenas de sensores IoT** que monitoram continuamente as condições ambientais. Neste projeto, simulo dados de **sensores PT100** – sensores de temperatura de alta precisão fixados no solo onde as plantas estão cultivadas.

Esses sensores fornecem leituras em tempo real que permitem:
- Monitorar a temperatura do solo onde os clones estão plantados
- Acionar sistemas automatizados como irrigação, aquecimento ou ventilação
- Manter condições ideais para o crescimento das mudas
- Prevenir perdas por variações bruscas de temperatura

Desenvolvi este projeto para simular um **pipeline de dados em tempo real** que:
1. Coleta dados de sensores PT100 simulados
2. Processa essas leituras usando tecnologias de streaming (Kafka e Spark)
3. Armazena as médias agregadas em um banco de dados PostgreSQL
4. Permite análise e visualização dos dados para tomada de decisões automatizadas

---

## Arquitetura

```
[Sensores PT100 Simulados]
        ↓
   Kafka (Producer)
        ↓
  Spark Structured Streaming (Consumer)
        ↓
   PostgreSQL (armazenamento final)
```

**Fluxo resumido:**
1. Simulo dados de sensores PT100 gerando leituras de temperatura do solo e umidade.  
2. As mensagens são publicadas continuamente no tópico Kafka `iot_sensors`.  
3. O Spark consome o tópico em *streaming*, calcula médias de temperatura/umidade por estufa e grava no Postgres.  
4. O Postgres mantém as leituras processadas, prontas para análise ou acionamento de sistemas automatizados.

---

## Tecnologias

| Componente | Função | Versão |
|-------------|--------|--------|
| Docker Compose | Orquestração dos serviços | latest |
| Zookeeper | Coordenação do cluster Kafka | 7.2.1 |
| Kafka | Mensageria em tempo real | 7.2.1 |
| Python | Simulação de sensores (producer) | 3.10 |
| Apache Spark | Processamento em streaming | 3.5.0 |
| PostgreSQL | Armazenamento relacional | 14 |

---

## Como rodar o projeto

### Pré-requisitos

- **Docker** e **Docker Compose** instalados na máquina
  - [Instalar Docker](https://docs.docker.com/get-docker/)
  - [Instalar Docker Compose](https://docs.docker.com/compose/install/)

### Passos

**Clone o repositório**
```bash
git clone https://github.com/cjohnnyl/docker-iot-project.git
cd docker-iot-project
```

**Suba os containers**
```bash
docker compose up -d --build
```

Isso vai iniciar:
- `zookeeper`
- `kafka`
- `postgres`
- `producer` (com script de espera para garantir que o Kafka esteja disponível)
- `spark`

> **Observação:** O producer utiliza um script `wait-for-kafka.sh` que aguarda o Kafka estar completamente inicializado antes de começar a publicar mensagens, evitando erros de conexão.

**Verifique se todos os serviços estão rodando**
```bash
docker ps
```

Você deve ver 5 containers com status `Up`:
- `zookeeper`
- `kafka`
- `postgres`
- `producer`
- `spark`

**Acompanhe os logs do producer**

Abra um terminal separado e monitore o producer para confirmar que ele está enviando dados:

```bash
docker logs -f producer
```

Aguarde até ver mensagens sendo publicadas (pode levar alguns segundos):
```
Kafka is unavailable - sleeping
Kafka is up - executing command
[Producer] Sent: {'sensor_id': 's1', 'estufa_id': 'EUCALIPTO_01', ...}
[Producer] Sent: {'sensor_id': 's2', 'estufa_id': 'EUCALIPTO_01', ...}
```

> **Nota:** Dados simulados de sensores PT100 de temperatura e umidade, publicados a cada 3 segundos no Kafka.

**Inicie o consumer do Spark**

**Somente depois** que o producer estiver enviando dados, abra outro terminal e inicie o consumer:

```bash
# entrar no container
docker exec -it spark bash

# dentro do container, iniciar o consumer
/opt/spark/bin/spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.6.0 /opt/spark-app/consumer/consumer.py
```

> **Importante:** Aguardar o producer estar ativo evita erros de tópico não encontrado no Kafka.

---

## Verificando o funcionamento

### Processamento do Consumer (Spark Streaming)

O consumer Spark realiza as seguintes operações:

1. **Leitura em streaming**: Consome mensagens do tópico `iot_sensors` do Kafka em tempo real
2. **Agregação por estufa**: Agrupa os dados por `estufa_id` 
3. **Cálculo de médias**: Calcula a média de `soil_temp_c` (temperatura do solo) e `humidity` (umidade) para cada estufa
4. **Gravação em batches**: A cada 10 segundos, persiste os dados agregados no PostgreSQL

**Exemplo de transformação:**
```
Dados brutos do Kafka (múltiplos sensores):
- sensor_id: s1, estufa_id: EUCALIPTO_01, soil_temp_c: 28.7, humidity: 67.4
- sensor_id: s2, estufa_id: EUCALIPTO_01, soil_temp_c: 25.3, humidity: 72.1
- sensor_id: s3, estufa_id: EUCALIPTO_01, soil_temp_c: 27.1, humidity: 68.9

Dados agregados gravados no Postgres:
- estufa_id: EUCALIPTO_01, avg_soil_temp_c: 27.03, avg_humidity: 69.47
```

Para ver os logs do processamento:
```bash
docker logs -f spark
```

Saída esperada:
```
Batch 0 gravado no Postgres com sucesso.
Batch 1 gravado no Postgres com sucesso.
```

---

### Consultando os dados no PostgreSQL

O banco de dados PostgreSQL armazena os dados processados na tabela `viveiro_iot`:

**Estrutura da tabela `viveiro_iot`:**
- `estufa_id`: Identificador da estufa
- `avg_soil_temp_c`: Média da temperatura do solo em °C (sensores PT100)
- `avg_humidity`: Média da umidade em %
- `processed_at`: Timestamp do processamento

**Comandos úteis:**

Listar as tabelas:
```bash
docker exec -it postgres psql -U postgres -d iot_data -c "\dt"
```

Consultar as últimas leituras agregadas:
```bash
docker exec -it postgres psql -U postgres -d iot_data -c "SELECT * FROM viveiro_iot ORDER BY processed_at DESC LIMIT 10;"
```

Exemplo de saída:
```
 estufa_id   |  avg_soil_temp_c  |  avg_humidity  |      processed_at       
--------------+-------------------+----------------+-------------------------
 EUCALIPTO_01 | 26.04             | 65.40          | 2025-11-10 00:22:40
 EUCALIPTO_01 | 26.03             | 65.32          | 2025-11-10 00:22:30
 EUCALIPTO_01 | 27.15             | 68.91          | 2025-11-10 00:22:20
```

**Interpretação dos dados:**

Aqui vemos as **médias agregadas** calculadas pelo Spark a cada 10 segundos. Esses valores permitem monitorar as condições do viveiro e acionar sistemas automatizados quando necessário (por exemplo, se a temperatura estiver fora do range ideal de 22-30°C, o sistema pode ativar a irrigação ou ventilação).

Verificar total de registros processados:
```bash
docker exec -it postgres psql -U postgres -d iot_data -c "SELECT COUNT(*) FROM viveiro_iot;"
```

---

## Estrutura do Projeto

```
docker-iot-project/
│
├── docker-compose.yml        # Orquestra todos os containers
├── producer/
│   ├── producer.py           # Gera e envia dados IoT para o Kafka
│   └── requirements.txt
│
├── spark/
│   ├── consumer.py           # Consome o tópico Kafka e grava no Postgres
│   └── Dockerfile            # Imagem customizada do Spark
│
└── README.md                 # Este arquivo
```
---

## Autor
**Carlos Johnny Leite**  
Engenheiro de Dados  
[github.com/cjohnnyl](https://github.com/cjohnnyl)
