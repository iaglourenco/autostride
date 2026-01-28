**STRIDE** é um modelo de *threat modeling* criado pela Microsoft para identificar riscos de segurança de forma sistemática. Não é ferramenta, não é checklist mágico, é uma lente para olhar a arquitetura e perguntar: “de que formas isso pode dar ruim?”.

STRIDE é um acrônimo com seis classes de ameaça:

**S — Spoofing (Falsificação de identidade)**
Alguém finge ser quem não é. Exemplos: uso de credenciais roubadas, tokens expostos, IAM mal configurado.
Mitigações típicas: autenticação forte, MFA, IAM com least privilege, validação de identidade.

**T — Tampering (Violação de integridade)**
Dados ou código são alterados sem autorização. Exemplos: alteração de payload em trânsito, arquivos em S3 sobrescritos.
Mitigações: TLS, hashes, assinatura digital, versionamento, controle de escrita.

**R — Repudiation (Repúdio)**
Ações sem rastreabilidade. O atacante faz algo e diz “não fui eu”.
Mitigações: logs imutáveis, CloudTrail, timestamps, correlação de eventos.

**I — Information Disclosure (Vazamento de informação)**
Dados sensíveis expostos. Exemplos: bucket público, secret no frontend, logs com dados pessoais.
Mitigações: criptografia em repouso e trânsito, Secrets Manager, políticas de acesso.

**D — Denial of Service (Negação de serviço)**
Indisponibilidade. Pode ser ataque ou erro de arquitetura.
Mitigações: rate limit, autoscaling, WAF, circuit breakers, quotas.

**E — Elevation of Privilege (Elevação de privilégio)**
Alguém começa com pouco acesso e termina como admin.
Mitigações: segregação de funções, revisão de policies, ausência de `*:*`, boundary policies.
