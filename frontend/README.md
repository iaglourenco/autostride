# AutoStride Frontend

Interface web para análise STRIDE automatizada de diagramas de arquitetura.

## Tecnologias

- **React** - Biblioteca JavaScript para construção de interfaces
- **Vite** - Build tool e dev server
- **Tailwind CSS** - Framework CSS utility-first
- **React Flow** - Biblioteca para visualização de grafos
- **Axios** - Cliente HTTP para comunicação com API

## Estrutura do Projeto

```txt
frontend/
├── src/
│   ├── components/
│   │   ├── ImageUpload.jsx       # Componente de upload de imagem
│   │   ├── GraphVisualization.jsx # Visualização do grafo com React Flow
│   │   └── StrideAnalysis.jsx    # Exibição da análise STRIDE
│   ├── App.jsx                    # Componente principal
│   ├── main.jsx                   # Entry point
│   └── index.css                  # Estilos globais (Tailwind)
├── package.json
├── vite.config.js
└── tailwind.config.js
```

## Instalação

```bash
cd frontend
npm install
```

## Desenvolvimento

Inicie o servidor de desenvolvimento:

```bash
npm run dev
```

A aplicação estará disponível em: **<http://localhost:5173/>**

## Como Usar

1. **Upload de Imagem**: Faça upload de um diagrama de arquitetura (PNG, JPG, JPEG)
2. **Visualização do Grafo**: Veja o grafo extraído automaticamente com os componentes detectados
3. **Análise STRIDE**: Analise as ameaças identificadas e suas recomendações

## Funcionalidades

### ImageUpload Component

- Drag & drop de imagens
- Preview da imagem selecionada
- Validação de tipo e tamanho
- Loading state durante processamento

### GraphVisualization Component

- Visualização interativa do grafo com React Flow
- Cores diferenciadas por tipo de componente
- Zoom, pan e minimap
- Exibição de confiança das detecções

### StrideAnalysis Component

- Resumo de ameaças por severidade e categoria
- Filtros por severidade e categoria STRIDE
- Cards coloridos por severidade
- Descrição detalhada e recomendações de mitigação

## Configuração

### API URL

Por padrão, o frontend se conecta ao backend em `http://localhost:8000`.

Para alterar, edite a constante `API_URL` em `src/App.jsx`:

```javascript
const API_URL = 'http://localhost:8000/api/v1/inference';
```

### Threshold de Confiança

Você pode ajustar o threshold de confiança das detecções (0.1 a 1.0) diretamente na interface.

## Componentes do Grafo

O sistema detecta os seguintes tipos de componentes:

- **boundary** - Limites do sistema (vermelho)
- **cache** - Cache (laranja)
- **database** - Banco de dados (azul)
- **external_service** - Serviço externo (roxo)
- **load_balancer** - Load balancer (verde)
- **monitoring** - Monitoramento (ciano)
- **security** - Segurança (laranja escuro)
- **service** - Serviço (índigo)
- **user** - Usuário (rosa)

## Categorias STRIDE

- **S**poofing - Falsificação de identidade
- **T**ampering - Adulteração de dados
- **R**epudiation - Repúdio de ações
- **I**nformation Disclosure - Divulgação de informações
- **D**enial of Service - Negação de serviço
- **E**levation of Privilege - Elevação de privilégios

## Build para Produção

```bash
npm run build
```

Os arquivos otimizados serão gerados na pasta `dist/`.

## Preview da Build

```bash
npm run preview
```

## Licença

MIT
