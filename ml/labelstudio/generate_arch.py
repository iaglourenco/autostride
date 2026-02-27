# Script para gerar datasets de imagens de arquitetura
import os
import random

os.environ["PATH"] += os.pathsep + r"C:\Program Files\Graphviz\bin"

from diagrams import Diagram, Cluster
from diagrams.aws.compute import EC2, Lambda, ECS, EKS
from diagrams.aws.database import RDS, Redshift, ElastiCache, Dynamodb, Aurora
from diagrams.aws.network import ELB, CloudFront, Route53, APIGateway
from diagrams.aws.security import WAF, Shield, IAM, SecretsManager
from diagrams.aws.management import Cloudwatch, CloudwatchEventTimeBased
from diagrams.aws.storage import S3
from diagrams.azure.compute import VM, FunctionApps, ContainerInstances, AppServices
from diagrams.azure.database import (
    SQLDatabases,
    CosmosDb,
    CacheForRedis,
    DatabaseForPostgresqlServers,
)
from diagrams.azure.network import (
    LoadBalancers,
    ApplicationGateway,
    FrontDoors,
    DNSZones,
    CDNProfiles,
)
from diagrams.azure.security import KeyVaults, SecurityCenter
from diagrams.azure.identity import ActiveDirectory
from diagrams.azure.devops import ApplicationInsights
from diagrams.azure.storage import BlobStorage
from diagrams.onprem.client import User, Users
from diagrams.generic.network import Firewall
from diagrams.generic.storage import Storage

CLASSES = [
    "boundary",
    "cache",
    "database",
    "external_service",
    "load_balancer",
    "monitoring",
    "security",
    "service",
    "user",
]

# Mapeamento de classes para componentes
COMPONENTS = {
    "user": [User, Users],
    "load_balancer": [ELB, CloudFront, LoadBalancers, ApplicationGateway, FrontDoors],
    "security": [
        WAF,
        Shield,
        Firewall,
        IAM,
        SecretsManager,
        KeyVaults,
        SecurityCenter,
        ActiveDirectory,
    ],
    "service": [
        EC2,
        Lambda,
        ECS,
        EKS,
        VM,
        FunctionApps,
        ContainerInstances,
        AppServices,
    ],
    "cache": [ElastiCache, CacheForRedis],
    "database": [
        RDS,
        Redshift,
        Dynamodb,
        Aurora,
        SQLDatabases,
        CosmosDb,
        DatabaseForPostgresqlServers,
    ],
    "monitoring": [Cloudwatch, CloudwatchEventTimeBased, ApplicationInsights],
    "external_service": [Route53, Storage, DNSZones, S3, BlobStorage, CDNProfiles],
    "boundary": [Firewall, WAF],
}


def generate_architecture(arch_id):
    """Gera uma arquitetura aleatória"""

    # Seleciona componentes aleatórios
    selected_classes = random.sample(CLASSES, k=random.randint(3, len(CLASSES)))

    filename = f"architecture-diagrams/train/gen_arch_{arch_id:04d}"

    with Diagram(
        f"Architecture {arch_id}", show=False, filename=filename, direction="LR"
    ):
        components = {}

        # Criar componentes para cada classe selecionada
        for cls in selected_classes:
            if cls in COMPONENTS:
                comp_class = random.choice(COMPONENTS[cls])
                label = cls.replace("_", " ").title()

                if cls in ["service"]:
                    # Serviços podem ter múltiplas instâncias
                    num_instances = random.randint(1, 3)
                    if num_instances > 1:
                        with Cluster(f"{label}s"):
                            components[cls] = [
                                comp_class(f"{label} {i+1}")
                                for i in range(num_instances)
                            ]
                    else:
                        components[cls] = comp_class(label)
                else:
                    components[cls] = comp_class(label)

        # Criar conexões lógicas entre componentes
        comp_list = list(components.items())

        # Padrão típico: user -> security/load_balancer -> service -> cache/database -> monitoring
        if "user" in components:
            user_comp = components["user"]

            # User se conecta ao security ou load_balancer
            next_comp = None
            for cls in ["security", "boundary", "load_balancer"]:
                if cls in components:
                    next_comp = components[cls]
                    _ = user_comp >> next_comp
                    break

            if next_comp is None and "service" in components:
                _ = user_comp >> components["service"]

        # Load balancer/Security -> Service
        for cls in ["load_balancer", "security", "boundary"]:
            if cls in components and "service" in components:
                _ = components[cls] >> components["service"]

        # Service -> Cache/Database
        if "service" in components:
            service = components["service"]
            for cls in ["cache", "database"]:
                if cls in components:
                    _ = service >> components[cls]

        # Monitoring observa outros componentes
        if "monitoring" in components:
            monitor = components["monitoring"]
            for cls, comp in components.items():
                if cls != "monitoring" and cls != "user":
                    if isinstance(comp, list):
                        _ = comp[0] >> monitor
                    else:
                        _ = comp >> monitor
                    break

        # External service pode se conectar a database ou service
        if "external_service" in components:
            ext = components["external_service"]
            if "database" in components:
                _ = ext >> components["database"]
            elif "service" in components:
                _ = ext >> components["service"]


# Gerar 50 imagens de arquitetura variadas
for i in range(50):
    generate_architecture(i + 1)
    print(f"Gerada arquitetura {i + 1}/50")

print("\nTodas as arquiteturas foram geradas com sucesso!")
