from typing import List, Dict, Set
from schemas.api_models import (
    Graph,
    Node,
    Edge,
    ThreatAnalysis,
    StrideAnalysisResult,
    ThreatSummary,
)


class StrideAnalyzer:
    """Analyzes a graph for STRIDE security threats."""

    def __init__(self):
        # Define threat rules by component type
        self.component_threats = {
            "user": [
                (
                    "Spoofing",
                    "High",
                    "Usuários podem ter suas identidades falsificadas sem autenticação robusta",
                    "Implementar autenticação multi-fator (MFA) e políticas de senha forte",
                ),
                (
                    "Repudiation",
                    "Medium",
                    "Ações do usuário podem não ser registradas adequadamente",
                    "Implementar sistema de logging e auditoria completo",
                ),
            ],
            "database": [
                (
                    "Tampering",
                    "High",
                    "Dados podem ser adulterados através de ataques de injeção SQL",
                    "Usar prepared statements, validação de entrada rigorosa e princípio do menor privilégio",
                ),
                (
                    "Information Disclosure",
                    "High",
                    "Dados sensíveis podem ser expostos sem criptografia adequada",
                    "Implementar criptografia em repouso (TDE) e em trânsito (TLS/SSL)",
                ),
            ],
            "cache": [
                (
                    "Information Disclosure",
                    "Medium",
                    "Dados em cache podem ser acessados sem criptografia",
                    "Criptografar dados sensíveis em cache e implementar TTL apropriado",
                ),
                (
                    "Tampering",
                    "Medium",
                    "Dados em cache podem ser adulterados",
                    "Implementar validação de integridade de dados em cache",
                ),
            ],
            "external_service": [
                (
                    "Spoofing",
                    "High",
                    "Serviços externos podem não ter sua origem validada",
                    "Implementar validação de certificados SSL/TLS e autenticação mútua",
                ),
                (
                    "Information Disclosure",
                    "Medium",
                    "Dados podem ser interceptados durante comunicação externa",
                    "Usar HTTPS/TLS para todas comunicações externas",
                ),
                (
                    "Denial of Service",
                    "Medium",
                    "Dependência de serviços externos pode causar indisponibilidade",
                    "Implementar circuit breakers, timeouts e fallback strategies",
                ),
            ],
            "load_balancer": [
                (
                    "Denial of Service",
                    "High",
                    "Load balancer pode ser sobrecarregado causando indisponibilidade",
                    "Implementar rate limiting, WAF e proteção DDoS",
                ),
                (
                    "Tampering",
                    "Medium",
                    "Tráfego pode ser interceptado ou modificado",
                    "Usar TLS/SSL para comunicação e validar integridade de requests",
                ),
            ],
            "monitoring": [
                (
                    "Information Disclosure",
                    "Low",
                    "Logs podem conter informações sensíveis",
                    "Implementar sanitização de logs e controle de acesso rigoroso",
                ),
                (
                    "Tampering",
                    "Low",
                    "Logs podem ser alterados para ocultar atividades maliciosas",
                    "Implementar logs imutáveis e assinaturas digitais",
                ),
            ],
            "security": [
                (
                    "Elevation of Privilege",
                    "High",
                    "Componentes de segurança podem ter vulnerabilidades permitindo bypass",
                    "Realizar testes de penetração regulares e manter componentes atualizados",
                ),
                (
                    "Tampering",
                    "High",
                    "Controles de segurança podem ser desabilitados ou alterados",
                    "Implementar integridade de código e monitoramento de mudanças",
                ),
            ],
            "service": [
                (
                    "Spoofing",
                    "Medium",
                    "Serviços podem não validar identidade de chamadores",
                    "Implementar autenticação de serviço-para-serviço (mTLS, JWT)",
                ),
                (
                    "Tampering",
                    "Medium",
                    "Dados processados podem ser adulterados",
                    "Validar entrada, usar assinaturas digitais para dados críticos",
                ),
                (
                    "Information Disclosure",
                    "Medium",
                    "Serviços podem expor informações sensíveis",
                    "Implementar controle de acesso e criptografia de dados",
                ),
                (
                    "Denial of Service",
                    "Medium",
                    "Serviços podem ser sobrecarregados",
                    "Implementar rate limiting, circuit breakers e scaling automático",
                ),
            ],
            "boundary": [
                (
                    "Tampering",
                    "High",
                    "Dados cruzando limites de confiança podem ser adulterados",
                    "Validar e sanitizar todos os dados que cruzam boundaries",
                ),
                (
                    "Information Disclosure",
                    "High",
                    "Dados sensíveis podem vazar através de boundaries",
                    "Implementar criptografia e controle de acesso em boundaries",
                ),
            ],
        }

    def analyze(self, graph: Graph) -> StrideAnalysisResult:
        """
        Perform comprehensive STRIDE analysis on the graph.

        Combines three approaches:
        1. Component-based: threats based on component type
        2. Flow-based: threats based on data flow between components
        3. Architectural patterns: holistic threats based on overall architecture
        """
        threats = []

        # Approach 1: Component-based analysis
        component_threats = self._analyze_by_component(graph.nodes)
        threats.extend(component_threats)

        # Approach 2: Flow-based analysis
        flow_threats = self._analyze_by_flow(graph)
        threats.extend(flow_threats)

        # Approach 3: Architectural pattern analysis
        pattern_threats = self._analyze_architectural_patterns(graph)
        threats.extend(pattern_threats)

        # Remove duplicate threats (same category + affected components)
        threats = self._deduplicate_threats(threats)

        # Generate summary
        summary = self._generate_summary(threats)

        return StrideAnalysisResult(threats=threats, summary=summary)

    def _analyze_by_component(self, nodes: List[Node]) -> List[ThreatAnalysis]:
        """Analyze threats based on component types."""
        threats = []

        for node in nodes:
            component_type = node.type
            if component_type in self.component_threats:
                for (
                    category,
                    severity,
                    description,
                    recommendation,
                ) in self.component_threats[component_type]:
                    threat = ThreatAnalysis(
                        category=category,
                        severity=severity,
                        affected_components=[node.id],
                        description=f"{component_type.replace('_', ' ').title()} ({node.id}): {description}",
                        recommendation=recommendation,
                    )
                    threats.append(threat)

        return threats

    def _analyze_by_flow(self, graph: Graph) -> List[ThreatAnalysis]:
        """Analyze threats based on data flow between components."""
        threats = []

        # Create node lookup
        node_map = {node.id: node for node in graph.nodes}

        # Check if there are security components in the graph
        has_security = any(node.type == "security" for node in graph.nodes)

        for edge in graph.edges:
            source = node_map.get(edge.source)
            target = node_map.get(edge.target)

            if not source or not target:
                continue

            # User to database without security component
            if source.type == "user" and target.type == "database":
                threat = ThreatAnalysis(
                    category="Elevation of Privilege",
                    severity="High",
                    affected_components=[edge.source, edge.target],
                    description=f"Acesso direto de usuário ({edge.source}) ao banco de dados ({edge.target}) sem camada de segurança",
                    recommendation="Adicionar camada de serviço intermediária e implementar controle de acesso rigoroso",
                )
                threats.append(threat)

                threat = ThreatAnalysis(
                    category="Information Disclosure",
                    severity="High",
                    affected_components=[edge.source, edge.target],
                    description=f"Dados sensíveis do banco de dados ({edge.target}) podem ser expostos diretamente ao usuário ({edge.source})",
                    recommendation="Implementar camada de abstração e filtrar dados sensíveis",
                )
                threats.append(threat)

            # Flow to external services
            if target.type == "external_service":
                threat = ThreatAnalysis(
                    category="Spoofing",
                    severity="High",
                    affected_components=[edge.source, edge.target],
                    description=f"Comunicação com serviço externo ({edge.target}) pode não validar autenticidade",
                    recommendation="Implementar validação de certificados, autenticação mútua e verificação de origem",
                )
                threats.append(threat)

                threat = ThreatAnalysis(
                    category="Tampering",
                    severity="Medium",
                    affected_components=[edge.source, edge.target],
                    description=f"Dados em trânsito para serviço externo ({edge.target}) podem ser interceptados",
                    recommendation="Usar TLS 1.3+ e validar integridade de dados (HMAC, assinaturas digitais)",
                )
                threats.append(threat)

            # Flow from external services
            if source.type == "external_service":
                threat = ThreatAnalysis(
                    category="Tampering",
                    severity="High",
                    affected_components=[edge.source, edge.target],
                    description=f"Dados recebidos de serviço externo ({edge.source}) podem estar comprometidos",
                    recommendation="Implementar validação rigorosa de entrada e sanitização de dados",
                )
                threats.append(threat)

            # Flow through boundaries
            if source.type == "boundary" or target.type == "boundary":
                boundary_node = (
                    edge.source if source.type == "boundary" else edge.target
                )
                other_node = edge.target if source.type == "boundary" else edge.source

                threat = ThreatAnalysis(
                    category="Tampering",
                    severity="High",
                    affected_components=[edge.source, edge.target],
                    description=f"Dados cruzando boundary ({boundary_node}) para {node_map[other_node].type} podem ser adulterados",
                    recommendation="Validar e sanitizar dados em ambos os lados do boundary, usar assinaturas digitais",
                )
                threats.append(threat)

            # Any flow without security component in path
            if (
                not has_security
                and source.type != "security"
                and target.type != "security"
            ):
                threat = ThreatAnalysis(
                    category="Spoofing",
                    severity="Medium",
                    affected_components=[edge.source, edge.target],
                    description=f"Fluxo de {source.type} ({edge.source}) para {target.type} ({edge.target}) sem autenticação explícita",
                    recommendation="Adicionar componente de segurança ou implementar autenticação no nível de serviço",
                )
                threats.append(threat)

        return threats

    def _analyze_architectural_patterns(self, graph: Graph) -> List[ThreatAnalysis]:
        """Analyze threats based on overall architectural patterns."""
        threats = []

        # Check for security components
        security_nodes = [node for node in graph.nodes if node.type == "security"]
        if not security_nodes:
            threat = ThreatAnalysis(
                category="Spoofing",
                severity="High",
                affected_components=[node.id for node in graph.nodes],
                description="Arquitetura não possui componente de segurança dedicado para autenticação/autorização",
                recommendation="Adicionar componente de segurança (API Gateway, Identity Provider, WAF)",
            )
            threats.append(threat)

        # Check for monitoring
        monitoring_nodes = [node for node in graph.nodes if node.type == "monitoring"]
        if not monitoring_nodes:
            threat = ThreatAnalysis(
                category="Repudiation",
                severity="Medium",
                affected_components=[node.id for node in graph.nodes],
                description="Arquitetura não possui componente de monitoring para auditabilidade",
                recommendation="Adicionar sistema de logging, monitoring e alertas (SIEM, observability platform)",
            )
            threats.append(threat)

        # Check for single points of failure (nodes with many incoming or outgoing edges)
        node_degrees = self._get_node_degrees(graph)
        for node_id, (in_degree, out_degree) in node_degrees.items():
            if in_degree + out_degree >= 5:  # Threshold for high connectivity
                node = next(n for n in graph.nodes if n.id == node_id)
                threat = ThreatAnalysis(
                    category="Denial of Service",
                    severity="High",
                    affected_components=[node_id],
                    description=f"Componente {node.type} ({node_id}) é um ponto central com alta conectividade - SPOF",
                    recommendation="Implementar redundância, load balancing e estratégias de failover",
                )
                threats.append(threat)

        # Check for databases without cache
        database_nodes = [node for node in graph.nodes if node.type == "database"]
        cache_nodes = [node for node in graph.nodes if node.type == "cache"]
        if database_nodes and not cache_nodes:
            threat = ThreatAnalysis(
                category="Denial of Service",
                severity="Medium",
                affected_components=[node.id for node in database_nodes],
                description="Bancos de dados sem camada de cache podem sofrer sobrecarga",
                recommendation="Adicionar camada de cache (Redis, Memcached) para reduzir carga no banco",
            )
            threats.append(threat)

        # Check for load balancer
        load_balancer_nodes = [
            node for node in graph.nodes if node.type == "load_balancer"
        ]
        service_nodes = [node for node in graph.nodes if node.type == "service"]
        if len(service_nodes) > 1 and not load_balancer_nodes:
            threat = ThreatAnalysis(
                category="Denial of Service",
                severity="Medium",
                affected_components=[node.id for node in service_nodes],
                description="Múltiplos serviços sem load balancer podem ter distribuição de carga inadequada",
                recommendation="Adicionar load balancer para distribuir tráfego de forma eficiente",
            )
            threats.append(threat)

        return threats

    def _get_node_degrees(self, graph: Graph) -> Dict[str, tuple]:
        """Calculate in-degree and out-degree for each node."""
        degrees = {node.id: [0, 0] for node in graph.nodes}  # [in_degree, out_degree]

        for edge in graph.edges:
            if edge.source in degrees:
                degrees[edge.source][1] += 1  # out_degree
            if edge.target in degrees:
                degrees[edge.target][0] += 1  # in_degree

        return {k: tuple(v) for k, v in degrees.items()}

    def _deduplicate_threats(
        self, threats: List[ThreatAnalysis]
    ) -> List[ThreatAnalysis]:
        """Remove duplicate threats based on category and affected components."""
        seen = set()
        unique_threats = []

        for threat in threats:
            # Create a key from category and sorted affected components
            key = (threat.category, tuple(sorted(threat.affected_components)))

            if key not in seen:
                seen.add(key)
                unique_threats.append(threat)

        return unique_threats

    def _generate_summary(self, threats: List[ThreatAnalysis]) -> ThreatSummary:
        """Generate summary statistics about threats."""
        by_severity = {"High": 0, "Medium": 0, "Low": 0}
        by_category = {
            "Spoofing": 0,
            "Tampering": 0,
            "Repudiation": 0,
            "Information Disclosure": 0,
            "Denial of Service": 0,
            "Elevation of Privilege": 0,
        }

        for threat in threats:
            by_severity[threat.severity] += 1
            by_category[threat.category] += 1

        return ThreatSummary(
            total_threats=len(threats), by_severity=by_severity, by_category=by_category
        )
