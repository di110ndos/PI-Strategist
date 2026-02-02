"""Deployment analyzer for continuous delivery strategy."""

from dataclasses import dataclass, field
from typing import Optional

from pi_strategist.models import (
    CapacityPlan,
    DEDDocument,
    DeploymentCluster,
    DeploymentStrategy,
    Task,
)


@dataclass
class DependencyGraph:
    """Graph of task dependencies."""

    nodes: set[str] = field(default_factory=set)
    edges: dict[str, set[str]] = field(default_factory=dict)  # task_id -> set of dependent task_ids

    def add_task(self, task_id: str):
        """Add a task node."""
        self.nodes.add(task_id)
        if task_id not in self.edges:
            self.edges[task_id] = set()

    def add_dependency(self, task_id: str, depends_on: str):
        """Add a dependency edge."""
        self.add_task(task_id)
        self.add_task(depends_on)
        self.edges[task_id].add(depends_on)

    def get_independent_tasks(self) -> set[str]:
        """Get tasks with no dependencies."""
        return {t for t in self.nodes if not self.edges.get(t)}

    def get_dependents(self, task_id: str) -> set[str]:
        """Get tasks that depend on the given task."""
        dependents = set()
        for t, deps in self.edges.items():
            if task_id in deps:
                dependents.add(t)
        return dependents


class DeploymentAnalyzer:
    """Analyzer for continuous delivery deployment strategy."""

    # Keywords for identifying domain boundaries
    DOMAIN_KEYWORDS = {
        "auth": ["auth", "login", "logout", "password", "session", "token", "oauth", "sso"],
        "user": ["user", "profile", "account", "settings", "preferences"],
        "payment": ["payment", "billing", "invoice", "subscription", "checkout", "cart"],
        "notification": ["notification", "email", "sms", "push", "alert", "message"],
        "analytics": ["analytics", "metrics", "dashboard", "report", "chart", "stats"],
        "admin": ["admin", "management", "configuration", "system"],
        "api": ["api", "endpoint", "rest", "graphql", "webhook"],
        "ui": ["ui", "component", "widget", "modal", "form", "button"],
        "data": ["database", "migration", "schema", "model", "entity"],
        "search": ["search", "filter", "query", "index"],
    }

    def __init__(self, cd_target_percentage: float = 0.30):
        """Initialize the deployment analyzer.

        Args:
            cd_target_percentage: Target percentage of tasks for early deployment (0.30 = 30%)
        """
        self.cd_target_percentage = cd_target_percentage

    def analyze(
        self,
        capacity_plan: CapacityPlan,
        ded: Optional[DEDDocument] = None,
    ) -> list[DeploymentCluster]:
        """Analyze tasks for deployment clustering.

        Args:
            capacity_plan: Parsed capacity plan with tasks
            ded: Optional DED document for additional context

        Returns:
            List of deployment clusters
        """
        all_tasks = capacity_plan.all_tasks

        # Build dependency graph
        graph = self._build_dependency_graph(all_tasks)

        # Identify independent task groups
        independent_tasks = graph.get_independent_tasks()

        # Cluster tasks by domain
        domain_clusters = self._cluster_by_domain(all_tasks, independent_tasks)

        # Convert to deployment clusters
        clusters = self._create_deployment_clusters(domain_clusters, all_tasks)

        return clusters

    def _build_dependency_graph(self, tasks: list[Task]) -> DependencyGraph:
        """Build a dependency graph from tasks."""
        graph = DependencyGraph()

        for task in tasks:
            graph.add_task(task.id)
            for dep in task.dependencies:
                graph.add_dependency(task.id, dep)

        return graph

    def _cluster_by_domain(
        self,
        all_tasks: list[Task],
        independent_tasks: set[str],
    ) -> dict[str, list[Task]]:
        """Cluster tasks by domain based on naming patterns."""
        clusters: dict[str, list[Task]] = {}

        for task in all_tasks:
            if task.id not in independent_tasks:
                continue

            domain = self._identify_domain(task)
            if domain not in clusters:
                clusters[domain] = []
            clusters[domain].append(task)

        return clusters

    def _identify_domain(self, task: Task) -> str:
        """Identify the domain for a task based on its name and tags."""
        text = f"{task.name} {' '.join(task.tags)}".lower()

        for domain, keywords in self.DOMAIN_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                return domain

        # Default domain based on story/epic if available
        if task.story_id:
            return f"story_{task.story_id}"

        return "general"

    def _create_deployment_clusters(
        self,
        domain_clusters: dict[str, list[Task]],
        all_tasks: list[Task],
    ) -> list[DeploymentCluster]:
        """Create deployment clusters from domain groupings."""
        clusters = []
        week = 1

        # Sort domains by number of tasks (deploy larger clusters first)
        sorted_domains = sorted(
            domain_clusters.items(),
            key=lambda x: len(x[1]),
            reverse=True,
        )

        for domain, tasks in sorted_domains:
            if len(tasks) < 2:
                continue  # Skip single-task clusters

            # Determine deployment strategy
            strategy = self._recommend_strategy(domain, tasks)

            # Create cluster
            cluster = DeploymentCluster(
                name=self._format_cluster_name(domain),
                tasks=tasks,
                strategy=strategy,
                deploy_timing=f"Week {week}",
                dependencies=self._find_cluster_dependencies(tasks, all_tasks),
                rollback_plan=self._generate_rollback_plan(strategy),
            )
            clusters.append(cluster)
            week += 1

        return clusters

    def _recommend_strategy(self, domain: str, tasks: list[Task]) -> DeploymentStrategy:
        """Recommend a deployment strategy based on domain and tasks."""
        # Domains that benefit from feature flags (can be toggled on/off)
        feature_flag_domains = {"ui", "user", "notification", "analytics", "search"}
        if domain in feature_flag_domains:
            return DeploymentStrategy.FEATURE_FLAG

        # High-risk or infrastructure domains should use full deployment
        # (auth, payment, data, api, admin need full testing before release)
        full_deployment_domains = {"auth", "payment", "data", "api", "admin"}
        if domain in full_deployment_domains:
            return DeploymentStrategy.FULL_DEPLOYMENT

        # Default to feature flag for flexibility
        return DeploymentStrategy.FEATURE_FLAG

    def _format_cluster_name(self, domain: str) -> str:
        """Format a human-readable cluster name."""
        name_map = {
            "auth": "Authentication & Security",
            "user": "User Profile & Settings",
            "payment": "Payment & Billing",
            "notification": "Notifications & Messaging",
            "analytics": "Analytics & Reporting",
            "admin": "Administration & Config",
            "api": "API Endpoints",
            "ui": "UI Components",
            "data": "Data & Migrations",
            "search": "Search & Filtering",
            "general": "General Features",
        }
        return name_map.get(domain, domain.replace("_", " ").title())

    def _find_cluster_dependencies(
        self,
        cluster_tasks: list[Task],
        all_tasks: list[Task],
    ) -> list[str]:
        """Find external dependencies for a cluster."""
        cluster_ids = {t.id for t in cluster_tasks}
        dependencies = set()

        for task in cluster_tasks:
            for dep in task.dependencies:
                if dep not in cluster_ids:
                    dependencies.add(dep)

        return list(dependencies)

    def _generate_rollback_plan(self, strategy: DeploymentStrategy) -> str:
        """Generate a rollback plan description for the strategy."""
        plans = {
            DeploymentStrategy.FEATURE_FLAG: "Disable feature flag to instantly revert",
            DeploymentStrategy.FULL_DEPLOYMENT: "Redeploy previous version via deployment pipeline",
        }
        return plans.get(strategy, "Manual rollback via deployment pipeline")

    def summary(
        self,
        clusters: list[DeploymentCluster],
        total_tasks: int,
    ) -> dict:
        """Generate summary of deployment analysis.

        Args:
            clusters: List of deployment clusters
            total_tasks: Total number of tasks in PI

        Returns:
            Summary dictionary
        """
        eligible_count = sum(len(c.tasks) for c in clusters)
        percentage = (eligible_count / total_tasks * 100) if total_tasks > 0 else 0
        target_met = percentage >= self.cd_target_percentage * 100

        strategy_counts: dict[str, int] = {}
        for cluster in clusters:
            strategy_name = cluster.strategy.value
            strategy_counts[strategy_name] = strategy_counts.get(strategy_name, 0) + 1

        return {
            "total_clusters": len(clusters),
            "eligible_tasks": eligible_count,
            "total_tasks": total_tasks,
            "cd_percentage": round(percentage, 1),
            "target_percentage": self.cd_target_percentage * 100,
            "target_met": target_met,
            "status": "ON TRACK" if target_met else "BELOW TARGET",
            "strategies": strategy_counts,
        }

    def get_deployment_timeline(
        self,
        clusters: list[DeploymentCluster],
    ) -> list[dict]:
        """Generate a deployment timeline.

        Args:
            clusters: List of deployment clusters

        Returns:
            List of timeline entries
        """
        timeline = []

        for cluster in clusters:
            timeline.append({
                "timing": cluster.deploy_timing,
                "cluster": cluster.name,
                "task_count": len(cluster.tasks),
                "strategy": cluster.strategy.value,
                "tasks": [{"id": t.id, "name": t.name} for t in cluster.tasks],
            })

        return timeline
