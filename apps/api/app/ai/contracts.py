"""Provider-independent AI contracts.

These Pydantic models are the *communication protocol* between agents. They are
deliberately independent of any LLM vendor and are exported as JSON Schema to
``packages/contracts/schemas`` so the frontend and external tools can code
against them.

Ownership:
- ``RobotSpecificationDraft`` is produced by the Robot Planner.
- Every downstream agent consumes the specification plus the artifacts it needs
  and adds exactly one artifact to the shared context.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import (
    AgentName,
    AgentResultStatus,
    CodeLanguage,
    Difficulty,
    DriveType,
    PrintMaterial,
    RobotType,
    StoreName,
    TargetPlatform,
)


class ContractModel(BaseModel):
    """Base for wire contracts: unknown fields are rejected to catch drift early."""

    model_config = ConfigDict(extra="forbid")


# ---------------------------------------------------------------------------
# Shared primitives
# ---------------------------------------------------------------------------


class Budget(ContractModel):
    min_usd: Decimal | None = Field(default=None, ge=0, description="Lower budget bound.")
    max_usd: Decimal | None = Field(default=None, ge=0, description="Upper budget bound.")
    currency: str = Field(default="USD", min_length=3, max_length=3)


class Dimensions(ContractModel):
    length_mm: float | None = Field(default=None, gt=0)
    width_mm: float | None = Field(default=None, gt=0)
    height_mm: float | None = Field(default=None, gt=0)


class RobotIdentification(ContractModel):
    """Result of the guided-flow research step before a project exists."""

    proposed_name: str = Field(min_length=1, max_length=120)
    robot_type: RobotType
    confidence: float = Field(ge=0, le=1)
    rationale: str = ""
    suggested_platform: TargetPlatform = TargetPlatform.ARDUINO
    suggested_difficulty: Difficulty = Difficulty.BEGINNER
    key_requirements: list[str] = Field(default_factory=list)
    needs_confirmation: bool = True


class BuildPreferences(ContractModel):
    """Persisted answers from the guided project flow.

    The configuration lives in ``project_configurations.configuration`` as JSON so
    it can evolve without a migration. Every downstream agent reads it through
    request parameters.
    """

    description: str = ""
    robot_name: str = ""
    robot_type: RobotType = RobotType.CUSTOM
    difficulty: Difficulty = Difficulty.BEGINNER
    shops: list[StoreName] = Field(default_factory=list)
    languages: list[CodeLanguage] = Field(
        default_factory=lambda: [CodeLanguage.PYTHON, CodeLanguage.CPP]
    )
    controllers: list[str] = Field(default_factory=list)
    controller_notes: str = ""
    custom_pcb: bool = False
    confirmed: bool = False
    budget_max_usd: Decimal | None = Field(default=None, ge=0)
    identification_rationale: str = ""
    identification_confidence: float = Field(default=0.0, ge=0, le=1)


class RobotSpecificationDraft(ContractModel):
    """Structured, buildable interpretation of the user's request."""

    summary: str = Field(min_length=1, description="One-paragraph description of the robot.")
    use_case: str = Field(default="", description="What the robot must do and where.")
    robot_type: RobotType = RobotType.CUSTOM
    difficulty: Difficulty = Difficulty.BEGINNER
    target_platform: TargetPlatform = TargetPlatform.UNDECIDED
    drive_type: DriveType = DriveType.NONE
    environment: str = "indoor"
    power_source: str = ""
    dimensions: Dimensions = Field(default_factory=Dimensions)
    payload_capacity_kg: Decimal | None = Field(default=None, ge=0)
    requirements: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    success_criteria: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0, le=1)


# ---------------------------------------------------------------------------
# Component Research Agent
# ---------------------------------------------------------------------------


class StoreOffer(ContractModel):
    """One store's estimate for a part, in Jordanian dinars."""

    store: StoreName
    label: str
    price_jod: Decimal = Field(ge=0)
    product_url: str = ""
    availability: str = "unknown"
    is_estimate: bool = True
    note: str = ""


class ComponentCandidate(ContractModel):
    name: str
    manufacturer: str = ""
    model_number: str = ""
    category: str
    specs: dict[str, Any] = Field(default_factory=dict)
    price_usd: Decimal | None = Field(default=None, ge=0)
    supplier: str = ""
    supplier_url: str | None = None
    availability: str = "unknown"
    compatibility_notes: list[str] = Field(default_factory=list)
    score: float = Field(default=0.0, ge=0, le=1)
    offers: list[StoreOffer] = Field(
        default_factory=list,
        description="Store estimates sorted cheapest to most expensive.",
    )
    cheapest_store: StoreName | None = None
    cheapest_price_jod: Decimal | None = Field(default=None, ge=0)


class BillOfMaterialsItem(ContractModel):
    """A required component slot, optionally resolved to a concrete candidate."""

    role: str = Field(description='e.g. "left drive motor", "main controller".')
    category: str
    quantity: int = Field(default=1, ge=1)
    required: bool = True
    selection: ComponentCandidate | None = None
    alternatives: list[ComponentCandidate] = Field(default_factory=list)
    rationale: str = ""


class ComponentResearchOutput(ContractModel):
    bill_of_materials: list[BillOfMaterialsItem] = Field(default_factory=list)
    unresolved_requirements: list[str] = Field(default_factory=list)
    compatibility_notes: list[str] = Field(default_factory=list)
    total_estimated_usd: Decimal | None = Field(default=None, ge=0)
    total_estimated_jod: Decimal | None = Field(default=None, ge=0)
    selected_shops: list[StoreName] = Field(default_factory=list)
    currency: str = "JOD"
    sources: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Electrical Engineering Agent
# ---------------------------------------------------------------------------


class ElectricalNodePin(ContractModel):
    """A physical pin surfaced for pin maps and netlist export."""

    name: str
    kind: str = "other"
    voltage_v: float | None = Field(default=None, ge=0)
    connected: bool = False


class ElectricalNode(ContractModel):
    ref: str = Field(description="Stable reference, e.g. U1, M1, BAT1.")
    label: str
    kind: Literal[
        "controller", "motor", "driver", "sensor", "power", "actuator", "regulator", "other"
    ] = "other"
    role: str = ""
    library_key: str = ""
    voltage_v: float | None = Field(default=None, ge=0)
    current_ma: float | None = Field(default=None, ge=0)
    peak_current_ma: float | None = Field(default=None, ge=0)
    pins: list[ElectricalNodePin] = Field(default_factory=list)
    notes: str = ""


class ElectricalConnection(ContractModel):
    from_ref: str
    from_pin: str
    to_ref: str
    to_pin: str
    net: str = ""
    signal: str = ""
    kind: Literal["power", "ground", "signal", "motor", "bus"] = "signal"
    voltage_v: float | None = Field(default=None, ge=0)
    wire_color: str = ""
    wire_gauge_awg: int | None = Field(default=None, ge=1, le=40)
    connector: str = ""
    notes: str = ""


class ElectricalIssue(ContractModel):
    """A deterministic validation finding shown before power is applied."""

    code: str
    severity: Literal["error", "warning", "info"]
    message: str
    refs: list[str] = Field(default_factory=list)
    remediation: str = ""


class PowerRail(ContractModel):
    name: str
    voltage_v: float | None = Field(default=None, ge=0)
    peak_current_ma: float | None = Field(default=None, ge=0)
    source_ref: str = ""
    notes: str = ""


class PowerBudget(ContractModel):
    supply_voltage_v: float | None = Field(default=None, ge=0)
    peak_current_ma: float | None = Field(default=None, ge=0)
    typical_current_ma: float | None = Field(default=None, ge=0)
    recommended_supply_ma: float | None = Field(default=None, ge=0)
    margin_percent: float | None = None
    usable_capacity_mah: float | None = Field(default=None, ge=0)
    estimated_runtime_min: float | None = Field(default=None, ge=0)


class PinDestination(ContractModel):
    """Where one physical pin terminates, including the wire it travels on."""

    ref: str
    pin: str
    net: str = ""
    signal: str = ""
    kind: str = "signal"
    connector: str = ""


class ElectricalPinoutEntry(ContractModel):
    """One row of the every-pin wiring table.

    A pin can fan out (for example a battery positive feeding a regulator and a
    motor driver), so destinations is a list rather than a single endpoint.
    Unconnected pins are still present with ``connected=False`` so the table is
    a complete inventory of the physical part.
    """

    ref: str
    part: str
    role: str = ""
    pin: str
    pin_kind: str = ""
    voltage_v: float | None = Field(default=None, ge=0)
    net: str = ""
    signal: str = ""
    connected: bool = False
    destinations: list[PinDestination] = Field(default_factory=list)
    wire_color: str = ""
    wire_gauge_awg: int | None = Field(default=None, ge=1, le=40)


class ElectricalPlan(ContractModel):
    nodes: list[ElectricalNode] = Field(default_factory=list)
    connections: list[ElectricalConnection] = Field(default_factory=list)
    pinout: list[ElectricalPinoutEntry] = Field(default_factory=list)
    power_budget: PowerBudget = Field(default_factory=PowerBudget)
    power_rails: list[PowerRail] = Field(default_factory=list)
    pin_map: dict[str, str] = Field(default_factory=dict)
    issues: list[ElectricalIssue] = Field(default_factory=list)
    safety_checks: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    wiring_steps: list[str] = Field(default_factory=list)
    design_notes: list[str] = Field(default_factory=list)
    library_version: str = "1.0"


# ---------------------------------------------------------------------------
# Programming Agent
# ---------------------------------------------------------------------------


class CodeFile(ContractModel):
    path: str
    language: str
    content: str
    explanation: str = ""


class LanguageBundle(ContractModel):
    """All files generated for one selected programming language."""

    language: CodeLanguage
    display_name: str
    framework: str = ""
    status: Literal["complete", "scaffold"] = "scaffold"
    files: list[CodeFile] = Field(default_factory=list)
    libraries: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class ProgrammingOutput(ContractModel):
    platform: TargetPlatform
    language: str = ""
    framework: str = ""
    files: list[CodeFile] = Field(default_factory=list)
    bundles: list[LanguageBundle] = Field(default_factory=list)
    libraries: list[str] = Field(default_factory=list)
    pin_assignments: dict[str, str] = Field(default_factory=dict)
    setup_steps: list[str] = Field(default_factory=list)
    upload_steps: list[str] = Field(default_factory=list)
    validation_notes: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Mechanical Design Agent
# ---------------------------------------------------------------------------


class MechanicalPart(ContractModel):
    name: str
    category: str = "structure"
    quantity: int = Field(default=1, ge=1)
    material: str = ""
    dimensions_mm: Dimensions = Field(default_factory=Dimensions)
    notes: str = ""


class AssemblyStep(ContractModel):
    order: int = Field(ge=1)
    title: str
    instructions: str
    tools: list[str] = Field(default_factory=list)
    parts: list[str] = Field(default_factory=list)
    safety_notes: list[str] = Field(default_factory=list)


class PrintMaterialQuote(ContractModel):
    """Cost to print the generated model in one material."""

    material: PrintMaterial
    price_per_gram_jod: Decimal = Field(ge=0)
    base_jod: Decimal = Field(ge=0)
    minimum_jod: Decimal = Field(ge=0)
    weight_g: Decimal = Field(ge=0)
    total_jod: Decimal = Field(ge=0)
    is_cheapest: bool = False


class MechanicalOutput(ContractModel):
    chassis: MechanicalPart | None = None
    parts: list[MechanicalPart] = Field(default_factory=list)
    assembly_steps: list[AssemblyStep] = Field(default_factory=list)
    drawings: list[str] = Field(
        default_factory=list, description="References/paths, not CAD payloads."
    )
    manufacturing_notes: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    dimensions_mm: Dimensions = Field(default_factory=Dimensions)
    volume_cm3: Decimal = Field(default=Decimal("0"), ge=0)
    infill_percent: int = Field(default=35, ge=0, le=100)
    stl_ascii: str = ""
    stl_filename: str = ""
    material_quotes: list[PrintMaterialQuote] = Field(default_factory=list)
    pricing_notes: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Cost Estimation Agent
# ---------------------------------------------------------------------------


class CostLineItem(ContractModel):
    label: str
    category: str = ""
    quantity: int = Field(default=1, ge=1)
    unit_price_usd: Decimal | None = Field(default=None, ge=0)
    line_total_usd: Decimal | None = Field(default=None, ge=0)
    unit_price_jod: Decimal | None = Field(default=None, ge=0)
    line_total_jod: Decimal | None = Field(default=None, ge=0)
    supplier: str = ""
    is_estimate: bool = True


class BudgetAlternative(ContractModel):
    description: str
    savings_usd: Decimal | None = None
    tradeoffs: list[str] = Field(default_factory=list)


class CostEstimate(ContractModel):
    line_items: list[CostLineItem] = Field(default_factory=list)
    subtotal_usd: Decimal | None = Field(default=None, ge=0)
    subtotal_jod: Decimal | None = Field(default=None, ge=0)
    shipping_usd: Decimal | None = Field(default=None, ge=0)
    contingency_usd: Decimal | None = Field(default=None, ge=0)
    print_cost_jod: Decimal | None = Field(default=None, ge=0)
    total_usd: Decimal | None = Field(default=None, ge=0)
    total_jod: Decimal | None = Field(default=None, ge=0)
    currency: str = "JOD"
    budget: Budget = Field(default_factory=Budget)
    budget_status: Literal["under", "within", "over", "unknown"] = "unknown"
    alternatives: list[BudgetAlternative] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Shared context and agent envelopes
# ---------------------------------------------------------------------------


class SharedProjectContext(ContractModel):
    """Accumulated artifacts passed between agents.

    This is the single source of truth during an orchestration run. Agents only
    write the field they own, which keeps independent development safe.
    """

    specification: RobotSpecificationDraft | None = None
    component_research: ComponentResearchOutput | None = None
    electrical: ElectricalPlan | None = None
    programming: ProgrammingOutput | None = None
    mechanical: MechanicalOutput | None = None
    cost: CostEstimate | None = None
    documentation: ProjectDocumentation | None = None
    artifacts: dict[str, Any] = Field(default_factory=dict)
    notes: list[str] = Field(default_factory=list)


class ProjectContext(ContractModel):
    """Input shared by every agent execution."""

    project_id: uuid.UUID
    project_name: str
    robot_type: RobotType
    description: str
    budget: Budget = Field(default_factory=Budget)
    shared: SharedProjectContext = Field(default_factory=SharedProjectContext)


class AgentRequest(ContractModel):
    context: ProjectContext
    parameters: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Per-agent input schemas (request.parameters validation targets)
# ---------------------------------------------------------------------------


class PlannerInput(ContractModel):
    description: str = Field(min_length=1)
    robot_type: RobotType = RobotType.CUSTOM
    skill_level: Difficulty = Difficulty.BEGINNER
    budget: Budget = Field(default_factory=Budget)
    constraints: list[str] = Field(default_factory=list)
    preferences: list[str] = Field(default_factory=list)


class ComponentResearchInput(ContractModel):
    specification: RobotSpecificationDraft
    budget: Budget = Field(default_factory=Budget)
    region: str = "global"
    preferred_suppliers: list[str] = Field(default_factory=list)


class ElectricalInput(ContractModel):
    specification: RobotSpecificationDraft
    component_research: ComponentResearchOutput


class ProgrammingInput(ContractModel):
    specification: RobotSpecificationDraft
    component_research: ComponentResearchOutput
    electrical: ElectricalPlan
    languages: list[CodeLanguage] = Field(
        default_factory=lambda: [CodeLanguage.PYTHON, CodeLanguage.CPP]
    )


class MechanicalInput(ContractModel):
    specification: RobotSpecificationDraft
    component_research: ComponentResearchOutput
    custom_pcb: bool = False


class CostInput(ContractModel):
    component_research: ComponentResearchOutput
    mechanical: MechanicalOutput | None = None
    budget: Budget = Field(default_factory=Budget)
    region: str = "global"
    quantity_multiplier: float = Field(default=1.0, gt=0, le=100)


class DocumentationFile(ContractModel):
    path: str
    title: str
    content: str


class ProjectDocumentation(ContractModel):
    files: list[DocumentationFile] = Field(default_factory=list)
    summary: str = ""
    notes: list[str] = Field(default_factory=list)


class TokenUsage(ContractModel):
    prompt_tokens: int = Field(default=0, ge=0)
    completion_tokens: int = Field(default=0, ge=0)
    latency_ms: int = Field(default=0, ge=0)


class AgentResult(ContractModel):
    """Normalized result every agent must return."""

    agent: AgentName
    status: AgentResultStatus
    summary: str = ""
    output: dict[str, Any] | None = None
    warnings: list[str] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
    usage: TokenUsage = Field(default_factory=TokenUsage)
    error: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


class OrchestrationResult(ContractModel):
    project_id: uuid.UUID
    status: AgentResultStatus
    results: list[AgentResult] = Field(default_factory=list)
    context: SharedProjectContext = Field(default_factory=SharedProjectContext)


class AgentDescriptor(ContractModel):
    """Static metadata for the agent catalog endpoint and UI."""

    name: AgentName
    display_name: str
    description: str
    status: Literal["placeholder", "available"] = "placeholder"
    depends_on: list[AgentName] = Field(default_factory=list)
    input_schema: str
    output_schema: str
    milestone: str
    owner_area: str
