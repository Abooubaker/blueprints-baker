#!/usr/bin/env python3
"""Configure the RoboCraft GitHub Project board.

Requires the `project` auth scope:

    gh auth refresh --hostname github.com -s project,read:project

The script is idempotent:
- adds/normalizes Status, Priority, Estimated Effort, and Development Area;
- adds every issue to the project if it is not already there;
- sets each item's fields from scripts/seed_github.py.

Project views are not exposed by the GitHub GraphQL API. The existing views
(Backlog, Priority board, Team items, Roadmap, My items) are documented in
docs/backlog.md and must be adjusted in the UI if desired.

Examples:
    python3 scripts/setup_project.py --dry-run
    python3 scripts/setup_project.py
"""

from __future__ import annotations

import argparse
import json
import runpy
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OWNER = "Abooubaker"
PROJECT_NUMBER = 1

STATUS_OPTIONS = [
    ("Backlog", "GRAY", "Not scheduled yet"),
    ("Ready", "BLUE", "Specified and unblocked"),
    ("In Progress", "YELLOW", "Actively being worked"),
    ("In Review", "PURPLE", "In review"),
    ("Done", "GREEN", "Completed"),
    ("Blocked", "RED", "Waiting on a dependency or decision"),
]
PRIORITY_OPTIONS = [
    ("P0 Critical", "RED", "Critical path, safety, or launch blocker"),
    ("P1 High", "ORANGE", "High priority"),
    ("P2 Medium", "YELLOW", "Medium priority"),
    ("P3 Low", "GRAY", "Low priority"),
]
EFFORT_FIELD = "Estimated Effort"
EFFORT_OPTIONS = [
    ("XS", "GRAY", "Under half a day"),
    ("S", "BLUE", "About one day"),
    ("M", "GREEN", "Two to three days"),
    ("L", "YELLOW", "About a week"),
    ("XL", "ORANGE", "More than a week"),
]
AREA_FIELD = "Development Area"
AREA_OPTIONS = [
    ("Frontend", "BLUE", "Next.js / React / UI"),
    ("Backend", "GREEN", "FastAPI / services / domain"),
    ("AI Agents", "PURPLE", "Agents, prompts, providers, evaluation"),
    ("Database", "YELLOW", "PostgreSQL, models, migrations, seeds"),
    ("DevOps", "ORANGE", "CI, deployment, observability, security"),
    ("Documentation", "GRAY", "Documentation and developer experience"),
    ("Design", "PINK", "UX, visual design, accessibility"),
]

AREA_MAP = {
    "frontend": "Frontend",
    "backend": "Backend",
    "ai": "AI Agents",
    "database": "Database",
    "devops": "DevOps",
    "docs": "Documentation",
    "design": "Design",
}
PRIORITY_MAP = {
    "p0": "P0 Critical",
    "p1": "P1 High",
    "p2": "P2 Medium",
    "p3": "P3 Low",
}
EFFORT_MAP = {
    "xs": "XS",
    "s": "S",
    "m": "M",
    "l": "L",
    "xl": "XL",
}

PROJECT_QUERY = """
query($owner: String!, $number: Int!) {
  user(login: $owner) {
    projectV2(number: $number) {
      id
      title
      fields(first: 50) {
        nodes {
          __typename
          ... on ProjectV2FieldCommon { id name }
          ... on ProjectV2SingleSelectField { options { id name } }
        }
      }
    }
  }
}
"""

UPDATE_SELECT_FIELD = """
mutation($fieldId: ID!, $name: String!, $options: [ProjectV2SingleSelectFieldOptionInput!]!) {
  updateProjectV2Field(
    input: {fieldId: $fieldId, name: $name, singleSelectOptions: $options}
  ) {
    projectV2Field {
      ... on ProjectV2SingleSelectField {
        id
        name
        options { id name }
      }
    }
  }
}
"""

CREATE_SELECT_FIELD = """
mutation($projectId: ID!, $name: String!, $options: [ProjectV2SingleSelectFieldOptionInput!]!) {
  createProjectV2Field(
    input: {
      projectId: $projectId
      dataType: SINGLE_SELECT
      name: $name
      singleSelectOptions: $options
    }
  ) {
    projectV2Field {
      ... on ProjectV2SingleSelectField {
        id
        name
        options { id name }
      }
    }
  }
}
"""

SET_ITEM_FIELDS = """
mutation(
  $projectId: ID!
  $itemId: ID!
  $statusField: ID!
  $status: String!
  $priorityField: ID!
  $priority: String!
  $effortField: ID!
  $effort: String!
  $areaField: ID!
  $area: String!
) {
  status: updateProjectV2ItemFieldValue(
    input: {projectId: $projectId, itemId: $itemId, fieldId: $statusField, value: {singleSelectOptionId: $status}}
  ) { projectV2Item { id } }
  priority: updateProjectV2ItemFieldValue(
    input: {projectId: $projectId, itemId: $itemId, fieldId: $priorityField, value: {singleSelectOptionId: $priority}}
  ) { projectV2Item { id } }
  effort: updateProjectV2ItemFieldValue(
    input: {projectId: $projectId, itemId: $itemId, fieldId: $effortField, value: {singleSelectOptionId: $effort}}
  ) { projectV2Item { id } }
  area: updateProjectV2ItemFieldValue(
    input: {projectId: $projectId, itemId: $itemId, fieldId: $areaField, value: {singleSelectOptionId: $area}}
  ) { projectV2Item { id } }
}
"""

ADD_ITEM = """
mutation($projectId: ID!, $contentId: ID!) {
  addProjectV2ItemById(input: {projectId: $projectId, contentId: $contentId}) {
    item { id }
  }
}
"""


def graphql(query: str, variables: dict[str, Any]) -> dict[str, Any]:
    payload = json.dumps({"query": query, "variables": variables})
    result = subprocess.run(
        ["gh", "api", "graphql", "--input", "-"],
        input=payload,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"gh api graphql failed:\n{result.stdout}\n{result.stderr}")
    data = json.loads(result.stdout)
    if data.get("errors"):
        raise RuntimeError(f"GraphQL errors: {json.dumps(data['errors'], indent=2)}")
    return data["data"]


def load_seed() -> dict[str, Any]:
    return runpy.run_path(str(ROOT / "scripts" / "seed_github.py"), run_name="seed_github")


def option_payload(
    options: list[tuple[str, str, str]], existing: list[dict[str, str]] | None = None
) -> list[dict[str, str]]:
    """Build option input, preserving existing option IDs by position.

    GitHub replaces the whole option list on update. Reusing IDs keeps item
    values intact when options are renamed in place.
    """
    payload: list[dict[str, str]] = []
    for index, (name, color, description) in enumerate(options):
        option = {"name": name, "color": color, "description": description}
        if existing and index < len(existing):
            option["id"] = existing[index]["id"]
        payload.append(option)
    return payload


def field_map(project: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {field["name"]: field for field in project["fields"]["nodes"]}


def single_select(field: dict[str, Any] | None) -> bool:
    return bool(field and field.get("__typename") == "ProjectV2SingleSelectField")


def ensure_select_field(
    project_id: str,
    fields: dict[str, dict[str, Any]],
    name: str,
    options: list[tuple[str, str, str]],
    *,
    rename_from: str | None = None,
    dry_run: bool,
) -> dict[str, Any]:
    actual_name = name if name in fields else (rename_from if rename_from and rename_from in fields else None)
    field = fields.get(actual_name) if actual_name else None
    desired = [option[0] for option in options]

    if field and not single_select(field):
        raise RuntimeError(f"Field {name!r} exists but is not single-select")

    if field:
        existing = [option["name"] for option in field.get("options", [])]
        needs_update = field["name"] != name or existing != desired
        if not needs_update:
            print(f"field ok: {name}")
            return field
        print(f"field update: {field['name']} -> {name} ({', '.join(desired)})")
        if dry_run:
            return field
        data = graphql(
            UPDATE_SELECT_FIELD,
            {
                "fieldId": field["id"],
                "name": name,
                "options": option_payload(options, field.get("options")),
            },
        )
        return data["updateProjectV2Field"]["projectV2Field"]

    print(f"field create: {name} ({', '.join(desired)})")
    if dry_run:
        return {"id": f"dry-{name}", "name": name, "options": [{"id": f"dry-{o}", "name": o} for o in desired]}
    data = graphql(
        CREATE_SELECT_FIELD,
        {"projectId": project_id, "name": name, "options": option_payload(options)},
    )
    return data["createProjectV2Field"]["projectV2Field"]


def item_map(project_id: str, seed: dict[str, Any], dry_run: bool) -> dict[str, str]:
    result = subprocess.run(
        [
            "gh",
            "project",
            "item-list",
            str(PROJECT_NUMBER),
            "--owner",
            OWNER,
            "--format",
            "json",
            "--limit",
            "200",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"gh project item-list failed:\n{result.stderr}")
    items = json.loads(result.stdout)["items"]
    by_title = {item["title"]: item["id"] for item in items}
    missing = [item.title for item in seed["ISSUES"] if item.title not in by_title]
    if not missing:
        print(f"items ok: {len(items)} present")
        return by_title

    print(f"items missing: {len(missing)}; adding")
    for title in missing:
        issue = next(item for item in seed["ISSUES"] if item.title == title)
        row = subprocess.run(
            ["gh", "issue", "list", "--repo", seed["REPO"], "--state", "all", "--search", f'"{title}" in:title', "--json", "number,title", "--limit", "10"],
            text=True,
            capture_output=True,
            check=False,
        )
        candidates = json.loads(row.stdout) if row.returncode == 0 else []
        match = next((c for c in candidates if c["title"] == title), None)
        if not match:
            raise RuntimeError(f"Could not find issue for {title!r}")
        if dry_run:
            print(f"  would add #{match['number']} {title}")
            by_title[title] = f"dry-{match['number']}"
            continue
        node = subprocess.run(
            [
                "gh",
                "api",
                "graphql",
                "-f",
                "query=query($number:Int!){repository(owner:\"Abooubaker\",name:\"robocraft\"){issue(number:$number){id}}}",
                "-F",
                f"number={match['number']}",
                "--jq",
                ".data.repository.issue.id",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        if node.returncode != 0:
            raise RuntimeError(f"Could not resolve issue node: {node.stderr}")
        data = graphql(ADD_ITEM, {"projectId": project_id, "contentId": node.stdout.strip()})
        by_title[title] = data["addProjectV2ItemById"]["item"]["id"]
        print(f"  added #{match['number']} {title}")
    return by_title


def board_status(issue: Any, seed: dict[str, Any]) -> str:
    if issue.close_after_create:
        return "Done"
    if any(not seed["ISSUE_BY_KEY"][dep].close_after_create for dep in issue.deps):
        return "Blocked"
    return "Ready"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Print the plan without mutations")
    args = parser.parse_args()

    seed = load_seed()
    data = graphql(PROJECT_QUERY, {"owner": OWNER, "number": PROJECT_NUMBER})
    project = data["user"]["projectV2"]
    project_id = project["id"]
    print(f"project: {project['title']} ({project_id})")
    fields = field_map(project)

    status = ensure_select_field(project_id, fields, "Status", STATUS_OPTIONS, dry_run=args.dry_run)
    priority = ensure_select_field(project_id, fields, "Priority", PRIORITY_OPTIONS, dry_run=args.dry_run)
    effort = ensure_select_field(
        project_id,
        fields,
        EFFORT_FIELD,
        EFFORT_OPTIONS,
        rename_from="Size",
        dry_run=args.dry_run,
    )
    area = ensure_select_field(project_id, fields, AREA_FIELD, AREA_OPTIONS, dry_run=args.dry_run)

    if args.dry_run:
        # Refetch is unnecessary; dry-run IDs are synthetic.
        pass
    else:
        refreshed = field_map(graphql(PROJECT_QUERY, {"owner": OWNER, "number": PROJECT_NUMBER})["user"]["projectV2"])
        status, priority, effort, area = (
            refreshed["Status"],
            refreshed["Priority"],
            refreshed[EFFORT_FIELD],
            refreshed[AREA_FIELD],
        )

    def option_id(field: dict[str, Any], name: str) -> str:
        for option in field.get("options", []):
            if option["name"] == name:
                return option["id"]
        raise RuntimeError(f"Missing option {name!r} on field {field['name']!r}")

    items = item_map(project_id, seed, args.dry_run)
    counts: Counter[str] = Counter()
    for issue in seed["ISSUES"]:
        status_name = board_status(issue, seed)
        priority_name = PRIORITY_MAP[issue.priority]
        effort_name = EFFORT_MAP[issue.effort]
        area_name = AREA_MAP[issue.area]
        counts[f"status:{status_name}"] += 1
        counts[f"priority:{priority_name}"] += 1
        counts[f"area:{area_name}"] += 1
        counts[f"effort:{effort_name}"] += 1

        if args.dry_run:
            print(f"  {issue.title}: {status_name} / {priority_name} / {effort_name} / {area_name}")
            continue

        graphql(
            SET_ITEM_FIELDS,
            {
                "projectId": project_id,
                "itemId": items[issue.title],
                "statusField": status["id"],
                "status": option_id(status, status_name),
                "priorityField": priority["id"],
                "priority": option_id(priority, priority_name),
                "effortField": effort["id"],
                "effort": option_id(effort, effort_name),
                "areaField": area["id"],
                "area": option_id(area, area_name),
            },
        )

    print("\nsummary")
    for key in sorted(counts):
        print(f"  {key}: {counts[key]}")
    print(f"  total items: {len(items)}")
    print("done" if not args.dry_run else "dry run complete")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except RuntimeError as error:
        print(f"error: {error}", file=sys.stderr)
        sys.exit(1)
