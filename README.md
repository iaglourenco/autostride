# AutoStride

Sistema automatizado de análise STRIDE para diagramas de arquitetura usando YOLO e React.
Desenvolvido como projeto do Hackaton do curso de pós graduação de Inteligência Artificial pela FIAP.

## Visão Geral

AutoStride é uma aplicação completa que permite fazer upload de diagramas de arquitetura de software e obter automaticamente:

1. **Detecção de Componentes**: Identifica componentes como databases, services, users, boundaries, etc.
2. **Construção de Grafo**: Cria um grafo conectando os componentes através das setas detectadas
3. **Análise STRIDE**: Realiza análise automática de ameaças usando a metodologia STRIDE

## Arquitetura

```txt
autostride/
├── backend/          # API FastAPI + YOLO
│   ├── main.py
│   ├── models/
│   ├── services/
│   └── schemas/
├── frontend/         # Interface React + Vite
│   └── src/
│       ├── components/
│       └── App.jsx
└── ml/              # Modelo YOLO treinado
    └── runs/detect/yolo11m-pose_manual/
```

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

## Instalação

### Instruções Backend

1. Instalar dependências Python:

```bash
cd backend
pip install -r requirements.txt
```

### Instruções Frontend

1. Instalar dependências Node:

```bash
cd frontend
npm install
```

## Executando a Aplicação

### 1. Iniciar o Backend

```bash
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

O backend estará disponível em:

- API: <http://localhost:8000>
- Documentação interativa: <http://localhost:8000/docs>

### 2. Iniciar o Frontend

Em outro terminal:

```bash
cd frontend
npm run dev
```

O frontend estará disponível em: <http://localhost:5173/> (ou 5174 se a porta estiver em uso)

## Como Usar

1. **Acesse a aplicação** em <http://localhost:5173/>
2. **Faça upload** de uma imagem do diagrama de arquitetura (PNG, JPG, JPEG)
3. **Aguarde o processamento** (~300-500ms)
4. **Visualize o grafo** extraído automaticamente com os componentes detectados
5. **Analise as ameaças STRIDE** identificadas e suas recomendações de mitigação

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
- Localização: `ml/runs/detect/yolo11m-pose_manual/weights/best.pt`
- Esse foi o melhor modelo encontrado após testes com diversos outros modelos e configurações.

## Licença

MIT
