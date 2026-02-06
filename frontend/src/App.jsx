import { useState } from 'react';
import axios from 'axios';
import ImageUpload from './components/ImageUpload';
import GraphVisualization from './components/GraphVisualization';
import StrideAnalysis from './components/StrideAnalysis';

const API_URL = 'http://localhost:8000/api/v1/inference';

function App() {
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('graph');
  const [confThreshold, setConfThreshold] = useState(0.5);

  const handleImageUpload = async (file) => {
    setLoading(true);
    setError(null);
    setResults(null);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await axios.post(
        `${API_URL}?conf_threshold=${confThreshold}&include_visualization=true`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );

      setResults(response.data);
      setActiveTab('detections');
    } catch (err) {
      console.error('Error uploading image:', err);
      setError(
        err.response?.data?.detail ||
          'Erro ao processar imagem. Verifique se o backend está rodando.'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">AutoSTRIDE</h1>
              <p className="mt-1 text-sm text-gray-600">
                Análise STRIDE Automatizada de Diagramas de Arquitetura
              </p>
            </div>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <label
                  htmlFor="conf-threshold"
                  className="text-sm text-gray-700"
                >
                  Threshold:
                </label>
                <input
                  id="conf-threshold"
                  type="number"
                  min="0.1"
                  max="1"
                  step="0.1"
                  value={confThreshold}
                  onChange={(e) => setConfThreshold(parseFloat(e.target.value))}
                  className="w-20 px-2 py-1 border border-gray-300 rounded-md text-sm"
                  disabled={loading}
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="space-y-8">
          {/* Upload Section */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              1. Upload do Diagrama
            </h2>
            <ImageUpload onImageUpload={handleImageUpload} loading={loading} />
          </div>

          {/* Error Display */}
          {error && (
            <div className="bg-red-50 border border-red-300 text-red-800 px-4 py-3 rounded-lg">
              <div className="flex items-center gap-2">
                <svg
                  className="h-5 w-5"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                    clipRule="evenodd"
                  />
                </svg>
                <span className="font-medium">Erro:</span>
                <span>{error}</span>
              </div>
            </div>
          )}

          {/* Results Section */}
          {results && (
            <div className="bg-white p-6 rounded-lg shadow space-y-6">
              {/* Metadata */}
              <div className="flex flex-wrap items-center gap-4 pb-4 border-b border-gray-200">
                <div className="text-sm text-gray-600">
                  <span className="font-medium">Modelo:</span>{' '}
                  {results.metadata.model_version}
                </div>
                <div className="text-sm text-gray-600">
                  <span className="font-medium">Detecções:</span>{' '}
                  {results.metadata.total_detections}
                </div>
                <div className="text-sm text-gray-600">
                  <span className="font-medium">Tempo:</span>{' '}
                  {results.metadata.processing_time_ms.toFixed(2)}ms
                </div>
                <div className="text-sm text-gray-600">
                  <span className="font-medium">Componentes:</span>{' '}
                  {results.graph.nodes.length}
                </div>
                <div className="text-sm text-gray-600">
                  <span className="font-medium">Conexões:</span>{' '}
                  {results.graph.edges.length}
                </div>
              </div>

              {/* Tabs */}
              <div className="border-b border-gray-200">
                <nav className="-mb-px flex space-x-8">
                  <button
                    onClick={() => setActiveTab('detections')}
                    className={`${
                      activeTab === 'detections'
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition-colors`}
                  >
                    2. Detecções YOLO
                  </button>
                  <button
                    onClick={() => setActiveTab('graph')}
                    className={`${
                      activeTab === 'graph'
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition-colors`}
                  >
                    3. Grafo da Arquitetura
                  </button>
                  <button
                    onClick={() => setActiveTab('stride')}
                    className={`${
                      activeTab === 'stride'
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition-colors`}
                  >
                    4. Análise STRIDE
                    <span className="ml-2 bg-red-100 text-red-800 text-xs font-semibold px-2 py-1 rounded-full">
                      {results.stride_analysis.summary.total_threats}
                    </span>
                  </button>
                </nav>
              </div>

              {/* Tab Content */}
              <div className="pt-4">
                {activeTab === 'detections' && (
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">
                      Detecções do Modelo YOLO
                    </h3>
                    {results.visualization ? (
                      <div className="bg-white p-4 rounded-lg border border-gray-300">
                        <img
                          src={results.visualization}
                          alt="YOLO Detections"
                          className="max-w-full h-auto mx-auto rounded-lg shadow-lg"
                        />
                        <p className="text-sm text-gray-600 mt-4 text-center">
                          Imagem com bounding boxes dos componentes e keypoints das setas detectados pelo YOLO
                        </p>
                      </div>
                    ) : (
                      <div className="bg-gray-50 p-8 rounded-lg border-2 border-dashed border-gray-300 text-center">
                        <p className="text-gray-500">Visualização não disponível</p>
                      </div>
                    )}
                  </div>
                )}

                {activeTab === 'graph' && (
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">
                      Grafo da Arquitetura
                    </h3>
                    <GraphVisualization graphData={results.graph} />
                  </div>
                )}

                {activeTab === 'stride' && (
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">
                      Análise de Ameaças STRIDE
                    </h3>
                    <StrideAnalysis strideData={results.stride_analysis} />
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Info Section */}
          {!results && !loading && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-blue-900 mb-2">
                Como usar
              </h3>
              <ol className="list-decimal list-inside space-y-2 text-blue-800">
                <li>Faça upload de uma imagem do diagrama de arquitetura</li>
                <li>
                  O sistema detectará os componentes e conexões automaticamente usando YOLO
                </li>
                <li>Visualize as detecções do modelo com bounding boxes e keypoints</li>
                <li>Explore o grafo da arquitetura construído automaticamente</li>
                <li>
                  Analise as ameaças STRIDE identificadas e suas recomendações
                </li>
              </ol>
              <div className="mt-4 text-sm text-blue-700">
                <strong>STRIDE:</strong> Spoofing, Tampering, Repudiation,
                Information Disclosure, Denial of Service, Elevation of
                Privilege
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Footer */}
      <div className="mt-12 pb-8 text-center text-sm text-gray-600">
        Feito com ❤️ por <a href='https://github.com/iaglourenco'>Iago Lourenço</a>
      </div>
    </div>
  );
}

export default App;
