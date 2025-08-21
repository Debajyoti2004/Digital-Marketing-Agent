import neo4j
import json
from rich import print as rprint
from rich.panel import Panel
import config

class KnowledgeGraph:
    def __init__(self):
        self._driver = None
        try:
            self._driver = neo4j.GraphDatabase.driver(
                config.NEO4J_URI,
                auth=(config.NEO4J_USER, config.NEO4J_PASSWORD)
            )
            self._driver.verify_connectivity()
            rprint(Panel.fit("[green]✅ Connected to Neo4j successfully[/green]"))
        except neo4j.exceptions.ServiceUnavailable as e:
            rprint(Panel.fit(f"[red]❌ Neo4j connection failed:[/red] {e}"))

    def close(self):
        if self._driver:
            self._driver.close()
            rprint(Panel.fit("[yellow]🔌 Neo4j connection closed[/yellow]"))

    def clean(self):
        if not self._driver:
            return
        with self._driver.session() as session:
            session.execute_write(self._delete_all)
            rprint(Panel.fit("[red]🧹 Knowledge graph cleared[/red]"))

    @staticmethod
    def _delete_all(tx):
        tx.run("MATCH (n) DETACH DELETE n")

    def find_successful_plan(self, user_command: str):
        if not self._driver:
            return None
        with self._driver.session() as session:
            result = session.execute_read(self._find_best_successful_plan, user_command)
            if result:
                rprint(Panel.fit(f"[cyan]♻️ Found successful plan for similar command:[/cyan] '{user_command}'"))
                if isinstance(result, str):
                    return json.loads(result)
                return result
            else:
                rprint(Panel.fit(f"[blue]🤔 No matching successful plan found for:[/blue] '{user_command}'"))
                return None

    @staticmethod
    def _find_best_successful_plan(tx, user_command):
        query = """
        MATCH (c:Command)-[r:HAS_SUCCESSFUL_PLAN]->(p:Plan)
        WITH c, p, r, apoc.text.levenshteinSimilarity(toLower(c.text), toLower($command)) AS sim
        WHERE sim > 0.6 AND NOT (c)-[:HAS_FAILED_PLAN]->(p)
        RETURN p.plan_json AS plan, sim, r.executions AS executions
        ORDER BY sim DESC, executions DESC
        LIMIT 1
        """
        result = tx.run(query, command=user_command)
        record = result.single()
        return record["plan"] if record else None

    def store_successful_plan(self, user_command: str, plan: list):
        if not self._driver:
            return
        plan_str = json.dumps(plan)
        with self._driver.session() as session:
            session.execute_write(self._store_success, user_command, plan_str)
            rprint(Panel.fit(f"[green]✅ Stored successful plan for:[/green] '{user_command}'"))

    @staticmethod
    def _store_success(tx, user_command, plan_str):
        query = """
        MERGE (c:Command {text: $command})
        MERGE (p:Plan {plan_json: $plan_str})
        MERGE (c)-[r:HAS_SUCCESSFUL_PLAN]->(p)
        ON CREATE SET r.executions = 1, r.last_executed = timestamp()
        ON MATCH SET r.executions = r.executions + 1, r.last_executed = timestamp()
        WITH c, p
        OPTIONAL MATCH (c)-[fr:HAS_FAILED_PLAN]->(p)
        DELETE fr
        """
        tx.run(query, command=user_command, plan_str=plan_str)

    def store_failed_plan(self, user_command: str, plan: list, feedback: str):
        if not self._driver:
            return
        plan_str = json.dumps(plan)
        with self._driver.session() as session:
            session.execute_write(self._store_failure, user_command, plan_str, feedback)
            rprint(Panel.fit(f"[yellow]⚠️ Stored failed plan with feedback for:[/yellow] '{user_command}'"))

    @staticmethod
    def _store_failure(tx, user_command, plan_str, feedback):
        query = """
        MERGE (c:Command {text: $command})
        MERGE (p:Plan {plan_json: $plan_str})
        MERGE (c)-[r:HAS_FAILED_PLAN]->(p)
        ON CREATE SET r.failures = 1, r.last_failed = timestamp(), r.last_feedback = $feedback
        ON MATCH SET r.failures = r.failures + 1, r.last_failed = timestamp(), r.last_feedback = $feedback
        """
        tx.run(query, command=user_command, plan_str=plan_str, feedback=feedback)

if __name__ == "__main__":
    kg = KnowledgeGraph()
    if not kg._driver:
        rprint(Panel.fit("[bold red]Cannot run tests without a Neo4j connection.[/bold red]"))
        exit()

    complex_success_command = "Find competitor prices for 'blue vase' and list my product on Amazon"
    complex_success_plan = [
        {"name": "market_search_for_products", "parameters": {"query": "blue ceramic vase price"}},
        {"name": "market_analyze_competitors", "parameters": {"data": "$tool_0_output"}},
        {"name": "amazon_create_or_update_listing", "parameters": {"product_name": "Artisan Blue Vase", "details": "$tool_1_output"}}
    ]
    kg.store_successful_plan(complex_success_command, complex_success_plan)
    retrieved_complex_plan = kg.find_successful_plan("Analyze competitors for blue vases and post to Amazon")
    if retrieved_complex_plan:
        rprint(Panel(f"[bold]Retrieved Plan:[/bold] {json.dumps(retrieved_complex_plan, indent=2)}"))
    else:
        rprint(Panel("[bold yellow]No sufficiently similar plan was retrieved for Test Case 1.[/bold yellow]"))

    failed_command = "Generate a website for me"
    failed_plan = [
        {"name": "website_generate_full_website", "parameters": {"site_title": "My Art Shop", "about_text": "Welcome!"}},
        {"name": "website_deploy", "parameters": {}}
    ]
    failure_feedback = "The website content was too generic and not what I wanted."
    kg.store_failed_plan(failed_command, failed_plan, failure_feedback)
    retrieved_failure = kg.find_successful_plan("Make a website for my art")
    if not retrieved_failure:
        rprint(Panel("[green]As expected, the previously failed website plan was not retrieved.[/green]"))

    correction_command = "Post a new marketing video to Facebook"
    correction_plan = [
        {"name": "design_create_promo_video", "parameters": {"topic": "New pottery collection"}},
        {"name": "facebook_post_video", "parameters": {"video_path": "$tool_0_output", "caption": "Check out our new pottery!"}}
    ]
    correction_feedback = "The first video it made was too short."
    kg.store_failed_plan(correction_command, correction_plan, correction_feedback)
    retrieved_correction = kg.find_successful_plan("Post a new marketing video to Facebook")
    if not retrieved_correction:
        rprint(Panel("[green]Success! The plan was not retrieved because it's marked as failed.[/green]"))
    kg.store_successful_plan(correction_command, correction_plan)
    retrieved_correction_success = kg.find_successful_plan("Post a new marketing video to Facebook")
    if retrieved_correction_success:
        rprint(Panel("[green]Success! The plan was retrieved, demonstrating the self-correction mechanism.[/green]"))
        rprint(Panel(f"[bold]Retrieved Plan:[/bold] {json.dumps(retrieved_correction_success, indent=2)}"))

    kg.close()
