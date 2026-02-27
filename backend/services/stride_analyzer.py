from typing import List, Dict, Set, Optional
from schemas.api_models import (
    Graph,
    Node,
    Edge,
    ThreatAnalysis,
    StrideAnalysisResult,
    ThreatSummary,
)


class StrideAnalyzer:
    """
    Analisa um grafo de arquitetura para ameaças STRIDE com consciência de contexto e hierarquia.
    """

    def __init__(self):
        # Regras base (Static Knowledge Base)
        self.kb_threats = {
            "database": {
                "Tampering": (
                    "High",
                    "Injeção SQL ou alteração não autorizada de dados persistidos.",
                ),
                "Information Disclosure": (
                    "Critical",
                    "Vazamento de dados sensíveis (PII, Segredos) em repouso.",
                ),
                "Denial of Service": (
                    "High",
                    "Esgotamento de conexões ou CPU do banco de dados.",
                ),
            },
            "service": {
                "Spoofing": (
                    "Medium",
                    "Impersonação de serviço ou falta de identidade (Service Mesh).",
                ),
                "Repudiation": ("Medium", "Falta de logs de transações de negócio."),
                "Elevation of Privilege": (
                    "High",
                    "Execução remota de código (RCE) ou permissões excessivas (IAM).",
                ),
            },
            "cache": {
                "Information Disclosure": (
                    "Medium",
                    "Dados em cache não criptografados.",
                ),
            },
            "external_service": {
                "Spoofing": (
                    "High",
                    "Dependência externa não verificada (Supply Chain Attack).",
                ),
                "Denial of Service": (
                    "Medium",
                    "Latência ou queda do serviço terceiro impactando a disponibilidade.",
                ),
            },
            "load_balancer": {
                "Denial of Service": (
                    "High",
                    "Ponto único de falha para ataques volumétricos.",
                ),
                "Information Disclosure": (
                    "Medium",
                    "Terminação SSL insegura ou logs de acesso expostos.",
                ),
            },
        }

    def analyze(self, graph: Graph) -> StrideAnalysisResult:
        threats = []

        # Mapa rápido para acesso aos nós
        node_map = {node.id: node for node in graph.nodes}

        # 1. Análise Contextual de Componentes (O nó em si)
        threats.extend(self._analyze_components(graph.nodes))

        # 2. Análise de Fluxo Hierárquico (O movimento do dado)
        threats.extend(self._analyze_flows(graph, node_map))

        # 3. Análise de Padrões Arquiteturais (A visão macro)
        threats.extend(self._analyze_architecture(graph, node_map))

        # Deduplicação e Sumário
        unique_threats = self._deduplicate_threats(threats)
        summary = self._generate_summary(unique_threats)

        return StrideAnalysisResult(threats=unique_threats, summary=summary)

    def _analyze_components(self, nodes: List[Node]) -> List[ThreatAnalysis]:
        threats = []
        for node in nodes:
            if node.type in self.kb_threats:
                for category, (base_severity, desc) in self.kb_threats[
                    node.type
                ].items():

                    # Ajuste de severidade baseado em confiança da detecção
                    final_severity = base_severity
                    note = ""
                    if node.confidence < 0.6:
                        final_severity = "Low"
                        note = " (Detectado com baixa confiança, verificar manual)"

                    threats.append(
                        ThreatAnalysis(
                            category=category,
                            severity=final_severity,
                            affected_components=[node.id],
                            description=f"{desc}{note}",
                            recommendation=self._get_recommendation(
                                category, node.type
                            ),
                        )
                    )
        return threats

    def _analyze_flows(
        self, graph: Graph, node_map: Dict[str, Node]
    ) -> List[ThreatAnalysis]:
        threats = []

        for edge in graph.edges:
            source = node_map.get(edge.source)
            target = node_map.get(edge.target)

            if not source or not target:
                continue

            # Se a flag cross_boundary vier True do GraphBuilder ou se os pais forem diferentes
            is_crossing = edge.cross_boundary or (source.parent_id != target.parent_id)

            if is_crossing:
                # Cenário 1: Internet -> Interno
                if source.type in ["user", "external_service"] and target.type not in [
                    "load_balancer",
                    "security",
                ]:
                    threats.append(
                        ThreatAnalysis(
                            category="Elevation of Privilege",
                            severity="Critical",
                            affected_components=[source.id, target.id],
                            description=f"Violação de Fronteira: Acesso direto de {source.type} externo para recurso interno {target.type} sem WAF/Gateway.",
                            recommendation="Colocar o recurso atrás de uma Private Subnet e expor apenas via Load Balancer/API Gateway.",
                        )
                    )

                # Cenário 2: Cruzamento genérico de boundary
                threats.append(
                    ThreatAnalysis(
                        category="Tampering",
                        severity="High",
                        affected_components=[source.id, target.id],
                        description=f"Fluxo cruza fronteira de confiança entre {source.type} e {target.type}. Dados podem ser interceptados.",
                        recommendation="Impor mTLS ou validação de JWT no ponto de entrada.",
                    )
                )

            # User -> Database Direto
            if source.type == "user" and target.type == "database":
                threats.append(
                    ThreatAnalysis(
                        category="Spoofing",
                        severity="Critical",
                        affected_components=[target.id],
                        description="Banco de dados exposto diretamente para usuários finais.",
                        recommendation="Remover acesso público do banco de dados imediatamente.",
                    )
                )

            # Service -> Database
            if source.type == "service" and target.type == "database":
                # Assumimos risco de injeção
                threats.append(
                    ThreatAnalysis(
                        category="Tampering",
                        severity="High",
                        affected_components=[target.id],
                        description="Serviço grava no banco de dados. Risco de SQL Injection.",
                        recommendation="Utilizar ORM ou Prepared Statements e aplicar Princípio do Menor Privilégio na role do banco.",
                    )
                )

            # Logs sensíveis (Flow -> Monitoring)
            if target.type == "monitoring":
                threats.append(
                    ThreatAnalysis(
                        category="Information Disclosure",
                        severity="Medium",
                        affected_components=[source.id],
                        description="Envio de dados para monitoramento pode conter PII ou Segredos.",
                        recommendation="Sanitizar logs e mascarar dados sensíveis antes do envio.",
                    )
                )

        return threats

    def _analyze_architecture(
        self, graph: Graph, node_map: Dict[str, Node]
    ) -> List[ThreatAnalysis]:
        threats = []

        # 1. Detecção de SPOF (Single Point of Failure)
        # Nós com muitas conexões de entrada, que não são LB
        in_degrees = {}
        for edge in graph.edges:
            in_degrees[edge.target] = in_degrees.get(edge.target, 0) + 1

        for node_id, degree in in_degrees.items():
            node = node_map[node_id]
            if degree > 3 and node.type in ["service", "database"]:
                threats.append(
                    ThreatAnalysis(
                        category="Denial of Service",
                        severity="High",
                        affected_components=[node_id],
                        description=f"Gargalo detectado: {node.type} recebe conexões de {degree} fontes diferentes.",
                        recommendation="Implementar Auto-Scaling Horizontal e Caching.",
                    )
                )

        # 2. Falta de Segurança em Profundidade
        has_security_layer = any(n.type == "security" for n in graph.nodes)
        has_public_access = any(n.type == "user" for n in graph.nodes)

        if has_public_access and not has_security_layer:
            threats.append(
                ThreatAnalysis(
                    category="Elevation of Privilege",
                    severity="High",
                    affected_components=[],
                    description="Arquitetura exposta a usuários públicos sem camada de Segurança explícita (WAF/Auth).",
                    recommendation="Adicionar Identity Provider (Cognito/Auth0) e WAF.",
                )
            )

        return threats

    def _get_recommendation(self, category: str, component_type: str) -> str:
        recs = {
            "Spoofing": "Implementar Autenticação Forte (MFA/Certificados).",
            "Tampering": "Assinatura digital e integridade de dados.",
            "Repudiation": "Logs auditáveis e centralizados com timestamp.",
            "Information Disclosure": "Criptografia (TLS 1.3 em trânsito, AES-256 em repouso).",
            "Denial of Service": "Rate Limiting, Throttling e CDN.",
            "Elevation of Privilege": "RBAC (Role Based Access Control) e Zero Trust.",
        }
        return recs.get(category, "Revisar controles de segurança.")

    def _deduplicate_threats(
        self, threats: List[ThreatAnalysis]
    ) -> List[ThreatAnalysis]:
        # Usa uma string de assinatura única para evitar duplicatas
        seen = set()
        unique = []
        for t in threats:
            # Assinatura: Categoria + Componentes Afetados Ordenados
            sig = f"{t.category}-{sorted(t.affected_components)}"
            if sig not in seen:
                seen.add(sig)
                unique.append(t)
        return unique

    def _generate_summary(self, threats: List[ThreatAnalysis]) -> ThreatSummary:
        counts = {"High": 0, "Medium": 0, "Low": 0, "Critical": 0}
        cats = {}
        for t in threats:
            counts[t.severity] = counts.get(t.severity, 0) + 1
            cats[t.category] = cats.get(t.category, 0) + 1

        return ThreatSummary(
            total_threats=len(threats), by_severity=counts, by_category=cats
        )
