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
- `producer`
- `spark`

> **Observação:** o container do Spark sobe “ocioso”. É preciso iniciar manualmente o *consumer* (próximo passo).

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
[Producer] Sent: {'sensor_id': 's1', 'estufa_id': 'EUCALIPTO_01', 'soil_temp_c': 28.7, 'humidity': 67.4, 'timestamp': '2025-11-10T00:22:35.970269'}
```

*Essas mensagens simulam sensores reais transmitindo dados de temperatura e umidade.*

---

### Logs do Spark (consumo e gravação no Postgres)
Mostra o Spark Structured Streaming consumindo o tópico Kafka e gravando micro-batches no banco.

```bash
docker logs -f spark
```

Saída esperada:
```
Batch 0 gravado no Postgres com sucesso.
Batch 1 gravado no Postgres com sucesso.
Batch 2 gravado no Postgres com sucesso.
```

*Aqui o Spark confirma que cada batch de dados foi processado e persistido no PostgreSQL.*

---

### Consultando os dados no PostgreSQL

Listar as tabelas:
```bash
docker exec -it postgres psql -U postgres -d iot_data -c "\dt"
```

Consultar as últimas leituras:
```bash
docker exec -it postgres psql -U postgres -d iot_data -c "SELECT * FROM iot_readings ORDER BY processed_at DESC LIMIT 10;"
```

Exemplo de saída:
```
 estufa_id   |  avg_soil_temp_c  |  avg_humidity  |      processed_at       
--------------+-------------------+----------------+-------------------------
 EUCALIPTO_01 | 26.04             | 65.40          | 2025-11-10 00:22:40
 EUCALIPTO_01 | 26.03             | 65.32          | 2025-11-10 00:22:30
 ...
```

*Esses dados são agregados em tempo real pelo Spark a partir das mensagens Kafka.*

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

## Demonstração sugerida (para o avaliador)

Durante a apresentação, seguir esta ordem:

1. **Mostrar o producer publicando dados IoT**
   ```bash
   docker logs -f producer
   ```
   → Sensores simulados enviando dados.

2. **Mostrar o spark consumindo e processando**
   ```bash
   docker logs -f spark
   ```
   → Batches processados e gravados no banco.

3. **Mostrar o Postgres com dados atualizados**
   ```bash
   docker exec -it postgres psql -U postgres -d iot_data -c "SELECT * FROM iot_readings ORDER BY processed_at DESC LIMIT 10;"
   ```
   → Leituras recentes, atualizadas a cada batch (~10 segundos).

4. (Opcional) **Mostrar o fluxo pelo Kafka diretamente**
   ```bash
   docker exec -it kafka bash
   kafka-console-consumer --bootstrap-server kafka:9092 --topic iot_topic --from-beginning
   ```

---

## Observações técnicas

- O Spark Structured Streaming processa micro-batches a cada 10 segundos (`trigger interval = 10000ms`).
- O Postgres armazena a média de temperatura e umidade por estufa.
- Todos os serviços são isolados via Docker, facilitando reprodutibilidade.
- Caso precise reiniciar:
  ```bash
  docker compose down
  docker compose up -d
  ```

---

## Próximos passos (opcional)
- Adicionar checkpoint no Spark (`.option("checkpointLocation", "/tmp/checkpoint")`).
- Automatizar a inicialização do consumer ajustando o `CMD` no `Dockerfile` do Spark.
- Criar dashboard em Streamlit ou Grafana conectado ao Postgres.
- Persistir dados do Kafka e Postgres em volumes Docker.

---

## Autor
**Carlos Johnny Leite**  
Engenheiro de Dados  
[github.com/cjohnnyl](https://github.com/cjohnnyl)
