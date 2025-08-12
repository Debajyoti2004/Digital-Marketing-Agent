from neo4j import GraphDatabase, exceptions
import json
from rich import print as rprint
from rich.panel import Panel
import config

class KnowledgeGraph:
    def __init__(self):
        self._driver = None
        try:
            self._driver = GraphDatabase.driver(
                config.NEO4J_URI, 
                auth=(config.NEO4J_USER, config.NEO4J_PASSWORD)
            )
            self._driver.verify_connectivity()
            rprint(Panel.fit("[green]Connected to Neo4j successfully[/green]"))
        except exceptions.ServiceUnavailable as e:
            rprint(Panel.fit(f"[red]Neo4j connection failed:[/red] {e}"))
    
    def close(self):
        if self._driver:
            self._driver.close()
            rprint(Panel.fit("[yellow]Neo4j connection closed[/yellow]"))

    def find_successful_plan(self, user_command):
        if not self._driver:
            return None
        with self._driver.session() as session:
            result = session.execute_read(self._find_plan, user_command)
            if result:
                rprint(Panel.fit(f"[cyan]Plan found for:[/cyan] {user_command}"))
            else:
                rprint(Panel.fit(f"[red]No matching plan found for:[/red] {user_command}"))
            return json.loads(result) if result else None

    @staticmethod
    def _find_plan(tx, user_command):
        query = """
        MATCH (c:Command)-[:HAS_SUCCESSFUL_PLAN]->(p:Plan)
        WITH c, p, apoc.text.levenshteinSimilarity(toLower(c.text), toLower($text)) AS sim
        WHERE sim > 0.7 OR toLower(c.text) CONTAINS toLower($text) OR toLower($text) CONTAINS toLower(c.text)
        RETURN p.steps
        ORDER BY sim DESC
        LIMIT 1
        """
        result = tx.run(query, text=user_command)
        record = result.single()
        return record["p.steps"] if record else None

    def store_successful_plan(self, user_command, plan):
        if not self._driver:
            return
        with self._driver.session() as session:
            session.execute_write(
                self._store_plan,
                user_command,
                json.dumps(plan, ensure_ascii=False)
            )
            rprint(Panel.fit(f"[green]Plan stored for:[/green] {user_command}"))

    @staticmethod
    def _store_plan(tx, user_command, plan_steps_json):
        query = """
        MERGE (c:Command {text: $text})
        MERGE (p:Plan {steps: $steps})
        MERGE (c)-[:HAS_SUCCESSFUL_PLAN]->(p)
        """
        tx.run(query, text=user_command, steps=plan_steps_json)


if __name__ == "__main__":
    kg = KnowledgeGraph()
    test_command = "get weather in London"
    test_plan = [
        {"tool": "SearchTool", "params": {"query": "current weather London"}},
        {"tool": "WeatherAPI", "params": {"location": "London", "units": "metric"}}
    ]
    kg.store_successful_plan(test_command, test_plan)
    retrieved_plan = kg.find_successful_plan("weather London")
    rprint(Panel.fit(f"[bold]Retrieved Plan:[/bold] {retrieved_plan}"))
    kg.close()
