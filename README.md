# AutoStride

Sistema automatizado de análise STRIDE para diagramas de arquitetura usando YOLO e React.
Desenvolvido como projeto do Hackaton do curso de pós graduação de Inteligência Artificial pela FIAP.

## Visão Geral

AutoStride é uma aplicação completa que permite fazer upload de diagramas de arquitetura de software e obter automaticamente:

1. **Detecção de Componentes**: Identifica componentes como databases, services, users, boundaries, etc.
2. **Construção de Grafo**: Cria um grafo conectando os componentes através das setas detectadas
3. **Análise STRIDE**: Realiza análise automática de ameaças usando a metodologia STRIDE

## Tecnologias

### Backend

- **FastAPI** - Framework web Python
- **Ultralytics YOLO** - Modelo de detecção de objetos e keypoints
- **OpenCV** - Processamento de imagens
- **Pydantic** - Validação de dados

### Frontend

- **React** - Biblioteca JavaScript para UI
- **Vite** - Build tool e dev server
- **Tailwind CSS** - Framework CSS
- **React Flow** - Visualização de grafos
- **Axios** - Cliente HTTP

## Executar com Docker

```bash
# Build e start
docker-compose build
docker-compose up -d

# Acessar
# Frontend: http://localhost:3000
# Backend: http://localhost:8000
# API Docs: http://localhost:8000/docs
# Modelos: http://localhost:8000/api/v1/models
```

### Seleção de Modelo

A API suporta múltiplos modelos. Use o parâmetro `model_name`:

```bash
# Listar modelos disponíveis
curl http://localhost:8000/api/v1/models

# Usar modelo específico
curl -X POST "http://localhost:8000/api/v1/inference?model_name=yolo11m-pose_manual_v3_v1" \
  -F "file=@diagram.png"
```

### Requisitos para GPU

- Docker Desktop ou Docker Engine
- [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)
- GPU NVIDIA com drivers CUDA

Para usar apenas CPU, remova a seção `deploy` do backend no `docker-compose.yml`.

## Funcionalidades

### Detecção de Componentes

O modelo YOLO detecta 9 tipos de componentes:

- **boundary** - Limites do sistema
- **cache** - Sistemas de cache
- **database** - Bancos de dados
- **external_service** - Serviços externos
- **load_balancer** - Load balancers
- **monitoring** - Sistemas de monitoramento
- **security** - Componentes de segurança
- **service** - Serviços internos
- **user** - Usuários/atores

Além disso, detecta **setas (fluxo_seta)** com 2 keypoints que representam conexões entre componentes.

### Análise STRIDE

O sistema realiza análise completa de ameaças em 3 níveis:

1. **Por tipo de componente**: Ameaças específicas baseadas no tipo (ex: databases → SQL injection)
2. **Por fluxo de dados**: Analisa conexões entre componentes (ex: user→database sem security)
3. **Padrões arquiteturais**: Identifica problemas sistêmicos (ex: falta de monitoring, SPOF)

#### Categorias STRIDE

- **S**poofing - Falsificação de identidade
- **T**ampering - Adulteração de dados
- **R**epudiation - Repúdio de ações
- **I**nformation Disclosure - Divulgação de informações
- **D**enial of Service - Negação de serviço
- **E**levation of Privilege - Elevação de privilégios

### Visualização do Grafo

- Grafo interativo com React Flow
- Cores diferenciadas por tipo de componente
- Zoom, pan e minimap
- Exibição da confiança das detecções

### Filtros e Análise

- Filtrar ameaças por severidade (High, Medium, Low)
- Filtrar por categoria STRIDE
- Descrição detalhada de cada ameaça
- Recomendações de mitigação específicas

## Endpoints da API

### `GET /health`

Health check do backend.

### `POST /api/v1/inference`

Endpoint principal para análise de diagramas.

**Query Parameters:**

- `conf_threshold` (float, 0.1-1.0): Threshold de confiança para detecções (padrão: 0.5)
- `include_visualization` (bool): Incluir visualização com detecções (padrão: false)

**Request:**

- `multipart/form-data` com campo `file` contendo a imagem

**Response:**

```json
{
  "graph": {
    "nodes": [...],
    "edges": [...]
  },
  "stride_analysis": {
    "threats": [...],
    "summary": {
      "total_threats": 48,
      "by_severity": {...},
      "by_category": {...}
    }
  },
  "metadata": {
    "processing_time_ms": 281.11,
    "model_version": "yolo11m-pose_manual",
    "total_detections": 24,
    "confidence_threshold": 0.5
  }
}
```

## Exemplo de Resultado

Para um diagrama com 17 componentes e 7 conexões:

- **Tempo de processamento**: ~280ms
- **Ameaças identificadas**: 48
  - Alta severidade: 20
  - Média severidade: 28
  - Baixa severidade: 0

## Configuração

### Ajustar Threshold de Confiança

No frontend, ajuste o slider na interface ou modifique o valor padrão em `frontend/src/App.jsx`:

```javascript
const [confThreshold, setConfThreshold] = useState(0.5);
```

### Alterar URL da API

Se o backend estiver em outro endereço, edite `frontend/src/App.jsx`:

```javascript
const API_URL = 'http://seu-servidor:8000/api/v1/inference';
```

## Modelo YOLO

O modelo YOLO11m-pose foi treinado especificamente para:

- Detectar componentes de arquitetura em diagramas
- Identificar keypoints de setas para construir conexões
