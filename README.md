# Projeto IoT – Viveiro de Eucalipto  
### *Streaming de dados em tempo real com Kafka, Spark e Postgres*

Este projeto simula um cenário de **monitoramento IoT em um viveiro de eucaliptos**, onde sensores enviam leituras contínuas de **temperatura do solo e umidade**, publicadas em tempo real em um **tópico Kafka**, processadas pelo **Apache Spark Structured Streaming** e armazenadas no **PostgreSQL**.

---

## Arquitetura

```
[Sensores simulados]
        ↓
   Kafka (Producer)
        ↓
  Spark Structured Streaming (Consumer)
        ↓
   PostgreSQL (armazenamento final)
```

**Fluxo resumido:**
1. O *producer* gera dados de sensores simulados (IoT).  
2. As mensagens são publicadas continuamente no tópico `iot_topic` do Kafka.  
3. O Spark consome o tópico em *streaming*, calcula médias de temperatura/umidade e grava no Postgres.  
4. O Postgres mantém as leituras processadas, prontas pra análise ou visualização.

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

> **Observação:** O container do Spark sobe "ocioso". É preciso iniciar manualmente o *consumer* (próximo passo).

**Inicie o consumer do Spark (manualmente)**  
Abra um terminal no container do Spark e execute o `spark-submit`:

```bash
# entrar no container
docker exec -it spark bash

# dentro do container, iniciar o consumer
/opt/spark/bin/spark-submit   --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.6.0   /opt/spark-app/consumer/consumer.py
```

> Dica: se o Kafka ainda estiver subindo, você pode ver erros temporários como `NoBrokersAvailable`. Espere alguns segundos e rode o comando novamente.

**(Opcional) UI do Spark**  
Com o consumer rodando, acesse a UI em: `http://localhost:4040` (porta já mapeada no `docker-compose`).

---

## Verificando o funcionamento

### Logs do Producer (envio de dados IoT)
Mostra as mensagens sendo publicadas no tópico Kafka.

```bash
docker logs -f producer
```

Saída esperada:
```
Kafka is unavailable - sleeping
Kafka is up - executing command
[Producer] Sent: {'sensor_id': 's1', 'estufa_id': 'EUCALIPTO_01', 'bed_id': 3, 'clone_id': 'CL234', 'soil_temp_c': 28.7, 'humidity': 67.4, 'timestamp': '2025-11-10T00:22:35.970269'}
[Producer] Sent: {'sensor_id': 's2', 'estufa_id': 'EUCALIPTO_01', 'bed_id': 7, 'clone_id': 'CL456', 'soil_temp_c': 25.3, 'humidity': 72.1, 'timestamp': '2025-11-10T00:22:38.970269'}
```

*Essas mensagens simulam sensores reais transmitindo dados de temperatura e umidade. Note que o producer primeiro aguarda o Kafka estar disponível antes de iniciar o envio.*

---

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
Batch 2 gravado no Postgres com sucesso.
```

*Cada batch representa um ciclo de 10 segundos de agregação e persistência dos dados.*

---

### Consultando os dados no PostgreSQL

O banco de dados PostgreSQL armazena duas tabelas:

**1. `iot_readings` - Dados agregados processados pelo Spark**
Contém as médias calculadas de temperatura e umidade por estufa:
- `estufa_id` (VARCHAR): Identificador da estufa
- `avg_soil_temp_c` (FLOAT): Média da temperatura do solo em °C
- `avg_humidity` (FLOAT): Média da umidade em %
- `processed_at` (TIMESTAMP): Data/hora do processamento do batch

**2. `viveiro_iot` - Tabela para dados brutos (uso futuro)**
Estrutura preparada para armazenar leituras individuais de sensores:
- `sensor_id`, `estufa_id`, `bed_id`, `clone_id`
- `soil_temp_c`, `humidity`, `timestamp`

**Comandos úteis:**

Listar as tabelas:
```bash
docker exec -it postgres psql -U postgres -d iot_data -c "\dt"
```

Consultar as últimas leituras agregadas:
```bash
docker exec -it postgres psql -U postgres -d iot_data -c "SELECT * FROM iot_readings ORDER BY processed_at DESC LIMIT 10;"
```

Exemplo de saída:
```
 estufa_id   |  avg_soil_temp_c  |  avg_humidity  |      processed_at       
--------------+-------------------+----------------+-------------------------
 EUCALIPTO_01 | 26.04             | 65.40          | 2025-11-10 00:22:40
 EUCALIPTO_01 | 26.03             | 65.32          | 2025-11-10 00:22:30
 EUCALIPTO_01 | 27.15             | 68.91          | 2025-11-10 00:22:20
```

Verificar total de registros processados:
```bash
docker exec -it postgres psql -U postgres -d iot_data -c "SELECT COUNT(*) FROM iot_readings;"
```

*Esses dados representam as médias calculadas em tempo real pelo Spark a partir dos múltiplos sensores IoT, atualizadas a cada 10 segundos.*

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
