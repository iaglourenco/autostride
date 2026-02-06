import { useState } from 'react';

const severityColors = {
  High: 'bg-red-100 text-red-800 border-red-300',
  Medium: 'bg-yellow-100 text-yellow-800 border-yellow-300',
  Low: 'bg-green-100 text-green-800 border-green-300',
};

const categoryColors = {
  Spoofing: 'bg-purple-100 text-purple-800',
  Tampering: 'bg-blue-100 text-blue-800',
  Repudiation: 'bg-pink-100 text-pink-800',
  'Information Disclosure': 'bg-orange-100 text-orange-800',
  'Denial of Service': 'bg-red-100 text-red-800',
  'Elevation of Privilege': 'bg-indigo-100 text-indigo-800',
};

const StrideAnalysis = ({ strideData }) => {
  const [selectedSeverity, setSelectedSeverity] = useState('all');
  const [selectedCategory, setSelectedCategory] = useState('all');

  if (!strideData) {
    return (
      <div className="h-96 flex items-center justify-center bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
        <p className="text-gray-500">Nenhuma análise para exibir</p>
      </div>
    );
  }

  const { threats, summary } = strideData;

  // Filter threats
  const filteredThreats = threats.filter((threat) => {
    if (selectedSeverity !== 'all' && threat.severity !== selectedSeverity) {
      return false;
    }
    if (selectedCategory !== 'all' && threat.category !== selectedCategory) {
      return false;
    }
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white p-4 rounded-lg shadow border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-700 mb-2">
            Total de Ameaças
          </h3>
          <p className="text-3xl font-bold text-gray-900">
            {summary.total_threats}
          </p>
        </div>

        <div className="bg-white p-4 rounded-lg shadow border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-700 mb-2">
            Por Severidade
          </h3>
          <div className="space-y-1">
            <div className="flex justify-between">
              <span className="text-red-600 font-medium">Alta:</span>
              <span className="font-bold">{summary.by_severity.High}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-yellow-600 font-medium">Média:</span>
              <span className="font-bold">{summary.by_severity.Medium}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-green-600 font-medium">Baixa:</span>
              <span className="font-bold">{summary.by_severity.Low}</span>
            </div>
          </div>
        </div>

        <div className="bg-white p-4 rounded-lg shadow border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-700 mb-2">
            Por Categoria STRIDE
          </h3>
          <div className="space-y-1 text-sm">
            {Object.entries(summary.by_category).map(([category, count]) => (
              <div key={category} className="flex justify-between">
                <span className="text-gray-600">{category.charAt(0)}:</span>
                <span className="font-semibold">{count}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white p-4 rounded-lg shadow border border-gray-200">
        <div className="flex flex-wrap gap-4">
          <div className="flex-1 min-w-[200px]">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Filtrar por Severidade
            </label>
            <select
              value={selectedSeverity}
              onChange={(e) => setSelectedSeverity(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">Todas</option>
              <option value="High">Alta</option>
              <option value="Medium">Média</option>
              <option value="Low">Baixa</option>
            </select>
          </div>

          <div className="flex-1 min-w-[200px]">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Filtrar por Categoria
            </label>
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">Todas</option>
              {Object.keys(summary.by_category).map((category) => (
                <option key={category} value={category}>
                  {category}
                </option>
              ))}
            </select>
          </div>
        </div>
        <div className="mt-2 text-sm text-gray-600">
          Exibindo {filteredThreats.length} de {threats.length} ameaças
        </div>
      </div>

      {/* Threats List */}
      <div className="space-y-4">
        {filteredThreats.map((threat, index) => (
          <div
            key={index}
            className={`p-4 rounded-lg border-2 ${
              severityColors[threat.severity]
            }`}
          >
            <div className="flex flex-wrap items-start justify-between gap-2 mb-2">
              <div className="flex flex-wrap items-center gap-2">
                <span
                  className={`px-3 py-1 rounded-full text-xs font-semibold ${
                    categoryColors[threat.category]
                  }`}
                >
                  {threat.category}
                </span>
                <span className="px-3 py-1 rounded-full text-xs font-semibold bg-gray-200 text-gray-700">
                  {threat.severity}
                </span>
              </div>
              <div className="text-xs text-gray-600">
                Componentes: {threat.affected_components.join(', ')}
              </div>
            </div>
            <h4 className="font-semibold text-gray-900 mb-2">
              {threat.description}
            </h4>
            <div className="text-sm text-gray-700">
              <span className="font-medium">Recomendação:</span>{' '}
              {threat.recommendation}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default StrideAnalysis;
