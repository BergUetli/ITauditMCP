"""
Seed script for COBIT 2019 framework data.

Populates the database with all 40 COBIT 2019 governance and management objectives
across 5 domains: EDM, APO, BAI, DSS, MEA.

Run this once to load COBIT 2019 into the knowledge base:
    python -m seeds.cobit_2019

NOTE FOR RP: Please review the title, description, objective, guidance, and
testing_procedure for each control. These are based on the published COBIT 2019
framework. Correct anything that doesn't match your audit experience.

KNOWN ISSUE: The input_gate.py regex pattern currently requires dot notation
(e.g., "BAI06.01"). Objective-level codes like "BAI06" won't be detected until
we update that regex. We'll fix that separately after verifying this seed works.
"""

import sys
import os

# Add the project root to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from knowledge.store import KnowledgeStore
from knowledge.models import Framework, Domain, Control, ControlType, AutomationLevel


def seed_cobit_2019() -> None:
    """
    Insert the full COBIT 2019 framework into the database.

    Creates one framework record, 5 domain records, and 40 control records.
    Prints progress to the console so you can see what's happening.
    Raises an exception and stops if anything fails.
    """
    store = KnowledgeStore()

    print("Starting COBIT 2019 seed...")

    # ----------------------------------------------------------------
    # STEP 1: Create the framework
    # ----------------------------------------------------------------

    print("\n[1/3] Creating framework...")

    framework = store.create_framework(Framework(
        slug="cobit_2019",
        name="COBIT 2019",
        version="2019",
        issuing_body="ISACA",
        scope=(
            "End-to-end IT governance and management framework. Covers how boards "
            "and executives govern IT, how management plans and organises IT, how IT "
            "solutions are built and deployed, how IT services are run, and how "
            "performance and compliance are monitored."
        ),
        is_certifiable=False,  # Organisations are assessed, not certified. Individuals can earn COBIT certifications.
    ))

    framework_id = framework.id
    print(f"  Created framework: {framework.name} (id: {framework_id})")

    # ----------------------------------------------------------------
    # STEP 2: Create the 5 domains
    # ----------------------------------------------------------------

    print("\n[2/3] Creating domains...")

    # EDM - Governance domain. Board and executive level.
    edm = store.create_domain(Domain(
        framework_id=framework_id,
        code="EDM",
        name="Evaluate, Direct and Monitor",
        description=(
            "The governance domain. Covers how the board and senior executives evaluate "
            "strategic options, direct IT activities, and monitor performance and compliance. "
            "These are governance objectives, not management objectives — the board owns them."
        ),
        hierarchy_level=1,
        sort_order=1,
    ))
    print(f"  Created domain: EDM (id: {edm.id})")

    # APO - Align, Plan and Organise. Senior management / IT leadership.
    apo = store.create_domain(Domain(
        framework_id=framework_id,
        code="APO",
        name="Align, Plan and Organise",
        description=(
            "Management domain for strategy, planning and organisational structure. "
            "Covers how IT management translates board direction into practical plans, "
            "manages risk, security, people, vendors, data and quality."
        ),
        hierarchy_level=1,
        sort_order=2,
    ))
    print(f"  Created domain: APO (id: {apo.id})")

    # BAI - Build, Acquire and Implement. Project and change management.
    bai = store.create_domain(Domain(
        framework_id=framework_id,
        code="BAI",
        name="Build, Acquire and Implement",
        description=(
            "Management domain for delivering IT solutions and changes. Covers "
            "programs, projects, requirements, development, availability, capacity, "
            "change management, knowledge, assets and configuration."
        ),
        hierarchy_level=1,
        sort_order=3,
    ))
    print(f"  Created domain: BAI (id: {bai.id})")

    # DSS - Deliver, Service and Support. IT operations.
    dss = store.create_domain(Domain(
        framework_id=framework_id,
        code="DSS",
        name="Deliver, Service and Support",
        description=(
            "Management domain for IT operations and service delivery. Covers day-to-day "
            "operations, incident and problem management, business continuity, security "
            "services, and ensuring business process controls work correctly."
        ),
        hierarchy_level=1,
        sort_order=4,
    ))
    print(f"  Created domain: DSS (id: {dss.id})")

    # MEA - Monitor, Evaluate and Assess. Oversight and assurance.
    mea = store.create_domain(Domain(
        framework_id=framework_id,
        code="MEA",
        name="Monitor, Evaluate and Assess",
        description=(
            "Management domain for oversight, compliance and assurance. Covers "
            "performance monitoring, internal control, regulatory compliance, and "
            "independent assurance. Feeds back into the governance layer."
        ),
        hierarchy_level=1,
        sort_order=5,
    ))
    print(f"  Created domain: MEA (id: {mea.id})")

    # ----------------------------------------------------------------
    # STEP 3: Create all 40 controls
    # ----------------------------------------------------------------

    print("\n[3/3] Creating controls...")

    controls = []

    # ================================================================
    # EDM DOMAIN — 5 governance objectives
    # ================================================================

    controls.append(Control(
        framework_id=framework_id,
        domain_id=edm.id,
        control_id_code="EDM01",
        title="Ensured Governance Framework Setting and Maintenance",
        description=(
            "Analyse and articulate the requirements for the governance of enterprise IT "
            "and put in place and maintain effective enabling structures, principles, "
            "processes and practices, with clarity of responsibilities and authority to "
            "achieve the enterprise's mission, goals and objectives."
        ),
        objective=(
            "Provide a consistent approach integrated with and aligned to the enterprise "
            "governance approach. Ensure that IT-related decisions are made in line with "
            "enterprise strategies and objectives. Ensure that IT-related processes are "
            "overseen effectively and transparently."
        ),
        guidance=(
            "The board should define and communicate what good IT governance looks like "
            "for the enterprise. This includes setting accountability structures, delegating "
            "authority clearly (who can make which IT decisions), and choosing a governance "
            "framework appropriate to the size and complexity of the organisation. "
            "Review the governance approach annually or when major changes occur."
        ),
        testing_procedure=(
            "1. Obtain the IT governance framework document and confirm it is board-approved. "
            "2. Verify accountability structures are documented (e.g., IT steering committee ToR). "
            "3. Confirm roles with IT decision-making authority are formally defined. "
            "4. Check evidence the framework has been reviewed in the past 12 months. "
            "5. Interview board members or governance committee members to confirm awareness."
        ),
        control_type=ControlType.PREVENTIVE,
        automation_level=AutomationLevel.MANUAL,
        aliases=["IT governance framework", "governance model", "IT oversight structure"],
    ))

    controls.append(Control(
        framework_id=framework_id,
        domain_id=edm.id,
        control_id_code="EDM02",
        title="Ensured Benefits Delivery",
        description=(
            "Optimise the value contribution to the business from the business processes, "
            "IT services and IT assets resulting from IT-enabled investments at acceptable costs."
        ),
        objective=(
            "Secure optimal value from IT-enabled initiatives, services and assets. Ensure "
            "that the expected business benefits are achieved and confirmed. Ensure that "
            "IT-enabled investments make the best use of resources."
        ),
        guidance=(
            "Establish a value management process that tracks benefits realisation for major "
            "IT investments. Benefits should be defined in measurable, business terms before "
            "a project starts — not just technical deliverables. The board should review a "
            "benefits realisation report at least annually. Link IT investment decisions to "
            "strategic objectives."
        ),
        testing_procedure=(
            "1. Select a sample of major IT investments from the past 2 years. "
            "2. For each: verify a benefits case was documented before approval. "
            "3. Check that post-implementation reviews were conducted. "
            "4. Compare actual benefits achieved to those originally forecast. "
            "5. Confirm board or steering committee reviewed benefits realisation reporting."
        ),
        control_type=ControlType.DETECTIVE,
        automation_level=AutomationLevel.MANUAL,
        aliases=["value management", "benefits realisation", "IT investment oversight"],
    ))

    controls.append(Control(
        framework_id=framework_id,
        domain_id=edm.id,
        control_id_code="EDM03",
        title="Ensured Risk Optimisation",
        description=(
            "Ensure that the enterprise's risk appetite and tolerance are understood, "
            "articulated and communicated, and that IT-related enterprise risk does not "
            "exceed the risk appetite and tolerance."
        ),
        objective=(
            "Ensure that IT-related risks do not exceed the board's risk appetite. "
            "Ensure risk management activities are integrated into business risk management. "
            "Ensure the board understands the IT risk profile."
        ),
        guidance=(
            "The board must formally set and document its IT risk appetite — the level of "
            "risk it is willing to accept in pursuit of objectives. IT risk should be "
            "reported to the board using business language (not technical jargon). Key "
            "risk indicators should be monitored and escalated when thresholds are breached. "
            "IT risk appetite should be reviewed when the business strategy changes."
        ),
        testing_procedure=(
            "1. Obtain the board-approved IT risk appetite statement. "
            "2. Verify the risk appetite has been communicated to IT management. "
            "3. Review the IT risk register for risks that exceed appetite and confirm "
            "they have board awareness and approved treatment plans. "
            "4. Check that IT risk is a standing agenda item at board or risk committee meetings. "
            "5. Confirm key risk indicators are defined, monitored and reported."
        ),
        control_type=ControlType.PREVENTIVE,
        automation_level=AutomationLevel.MANUAL,
        aliases=["risk appetite", "IT risk governance", "risk tolerance"],
    ))

    controls.append(Control(
        framework_id=framework_id,
        domain_id=edm.id,
        control_id_code="EDM04",
        title="Ensured Resource Optimisation",
        description=(
            "Ensure that adequate and sufficient IT-related capabilities (people, process, "
            "technology) are available to support enterprise objectives effectively and "
            "at an optimal cost."
        ),
        objective=(
            "Ensure the enterprise has the IT capabilities it needs. Avoid underinvestment "
            "(gaps in capability) and overinvestment (wasted spend). Ensure IT resource "
            "allocation aligns with strategic priorities."
        ),
        guidance=(
            "The board should satisfy itself that IT management has a clear picture of "
            "current and required IT capabilities. This means reviewing IT capacity plans, "
            "skills assessments, and technology roadmaps. Key questions: Do we have the "
            "right people? The right tools? Are we investing in the right areas? Are we "
            "over-relying on specific vendors or individuals?"
        ),
        testing_procedure=(
            "1. Obtain the IT resource plan or capacity plan for the current year. "
            "2. Confirm it has been reviewed and approved by senior management or the board. "
            "3. Check for evidence of skills gap analysis and remediation plans. "
            "4. Review vendor dependency assessments (single points of failure). "
            "5. Confirm IT budgets align to strategic priorities identified in the IT strategy."
        ),
        control_type=ControlType.PREVENTIVE,
        automation_level=AutomationLevel.MANUAL,
        aliases=["resource management", "IT capacity governance", "capability planning"],
    ))

    controls.append(Control(
        framework_id=framework_id,
        domain_id=edm.id,
        control_id_code="EDM05",
        title="Ensured Stakeholder Engagement",
        description=(
            "Ensure that enterprise IT stakeholders are identified, that their engagement "
            "needs are understood, and that stakeholders are involved in appropriate IT "
            "governance activities. Ensure reporting and communication to stakeholders "
            "is transparent, accurate and timely."
        ),
        objective=(
            "Ensure stakeholders (board, executives, business units, regulators, external "
            "parties) have the IT information they need. Ensure reporting is accurate and "
            "not misleading. Ensure complaints and concerns from stakeholders are captured "
            "and addressed."
        ),
        guidance=(
            "Map your IT stakeholders and understand what each group needs to know about IT. "
            "Regulators need compliance evidence. The board needs risk and performance "
            "summaries. Business units need service performance data. Establish formal "
            "reporting cycles and confirm reports are reviewed. Ensure there is a mechanism "
            "for stakeholders to raise concerns about IT."
        ),
        testing_procedure=(
            "1. Obtain the IT stakeholder communication plan or reporting calendar. "
            "2. Select a sample of reports (board pack, regulator reports, business unit "
            "dashboards) and verify they were issued on schedule. "
            "3. Check that a process exists for stakeholders to raise IT concerns or complaints. "
            "4. Review a sample of concerns raised and confirm they were addressed. "
            "5. Confirm regulatory reporting obligations are known and met."
        ),
        control_type=ControlType.DETECTIVE,
        automation_level=AutomationLevel.MANUAL,
        aliases=["stakeholder reporting", "IT communication", "governance transparency"],
    ))

    # ================================================================
    # APO DOMAIN — 14 management objectives
    # ================================================================

    controls.append(Control(
        framework_id=framework_id,
        domain_id=apo.id,
        control_id_code="APO01",
        title="Managed I&T Management Framework",
        description=(
            "Clarify and maintain the mission and vision of IT. Implement and maintain "
            "mechanisms and authorities for the management of information and technology, "
            "and support achievement of enterprise objectives."
        ),
        objective=(
            "Provide a consistent management approach for enterprise I&T that enables "
            "the enterprise's governance requirements to be met. Ensure processes, roles "
            "and responsibilities are clearly defined and operated effectively."
        ),
        guidance=(
            "Establish a clear IT operating model — how IT is organised, who is responsible "
            "for what, and how IT decisions are escalated. Define and maintain an IT policy "
            "framework (what policies exist, who owns them, how often they're reviewed). "
            "Ensure roles and responsibilities for all significant IT activities are documented "
            "and understood. Keep an organisational chart for IT and a RACI for key processes."
        ),
        testing_procedure=(
            "1. Obtain the IT organisational chart and confirm it is current. "
            "2. Verify key IT roles have documented job descriptions or RACI assignments. "
            "3. Review the IT policy register — confirm all policies have owners and review dates. "
            "4. Select a sample of policies and verify they have been reviewed within the required cycle. "
            "5. Confirm there is a process for employees to acknowledge and access IT policies."
        ),
        control_type=ControlType.PREVENTIVE,
        automation_level=AutomationLevel.MANUAL,
        aliases=["IT operating model", "IT policy framework", "IT organisation structure"],
    ))

    controls.append(Control(
        framework_id=framework_id,
        domain_id=apo.id,
        control_id_code="APO02",
        title="Managed Strategy",
        description=(
            "Provide a holistic view of the current business and IT environment, the future "
            "direction, and the initiatives required to migrate to the desired future environment. "
            "Leverage enterprise architecture building blocks and components, including externally "
            "sourced services and related capabilities."
        ),
        objective=(
            "Provide an IT strategy that is aligned to the enterprise strategy. Ensure IT "
            "investments and activities support enterprise objectives. Identify emerging "
            "technology opportunities and risks."
        ),
        guidance=(
            "Produce an IT strategy document that links directly to business strategy. It "
            "should cover: where we are now (current state), where we want to be (target state), "
            "and how we get there (roadmap). Refresh the strategy at least annually or when "
            "business strategy changes materially. Present the IT strategy to the board for "
            "approval. Ensure the strategy includes a budget plan."
        ),
        testing_procedure=(
            "1. Obtain the current IT strategy document. "
            "2. Verify it was reviewed and approved within the last 12-18 months. "
            "3. Check that IT strategic objectives are traceable to business objectives. "
            "4. Review the IT strategy roadmap and confirm progress is tracked. "
            "5. Confirm budget/resource allocation is aligned to strategy priorities."
        ),
        control_type=ControlType.PREVENTIVE,
        automation_level=AutomationLevel.MANUAL,
        aliases=["IT strategy", "technology roadmap", "IT strategic plan"],
    ))

    controls.append(Control(
        framework_id=framework_id,
        domain_id=apo.id,
        control_id_code="APO03",
        title="Managed Enterprise Architecture",
        description=(
            "Establish a common architecture comprising business process, information, "
            "data, application and technology architecture layers, based on enterprise "
            "and IT strategy. Provide a standard, responsive and efficient delivery of "
            "operational and strategic objectives."
        ),
        objective=(
            "Represent the different building blocks that make up the enterprise and its "
            "interrelationships, as well as the principles guiding their design and "
            "evolution over time, to enable a standard, responsive and efficient delivery "
            "of operational and strategic objectives."
        ),
        guidance=(
            "Maintain an enterprise architecture that documents the business processes, "
            "data flows, applications and technology infrastructure. This is the 'map' of "
            "how the enterprise's IT works. It is used to evaluate new investments, "
            "identify duplication, and manage complexity. In smaller organisations this "
            "can be a simple set of diagrams; in larger ones it requires dedicated tools "
            "and an architecture team."
        ),
        testing_procedure=(
            "1. Obtain the enterprise architecture documentation (or equivalent). "
            "2. Verify it covers all four layers: business, information, application, technology. "
            "3. Confirm there is a process for new IT projects to be reviewed against the architecture. "
            "4. Check that deviations from architecture standards require approval. "
            "5. Verify architecture documentation is updated when significant changes occur."
        ),
        control_type=ControlType.PREVENTIVE,
        automation_level=AutomationLevel.MANUAL,
        aliases=["enterprise architecture", "IT architecture", "EA"],
    ))

    controls.append(Control(
        framework_id=framework_id,
        domain_id=apo.id,
        control_id_code="APO04",
        title="Managed Innovation",
        description=(
            "Maintain an awareness of information and technology trends. Identify innovation "
            "opportunities, and plan how to benefit from innovation in relation to business needs."
        ),
        objective=(
            "Achieve competitive advantage, business innovation or improved operational "
            "effectiveness and efficiency by exploiting information technology developments. "
            "Identify opportunities for IT-enabled innovation to support enterprise strategy."
        ),
        guidance=(
            "Establish a process for monitoring emerging technology trends (cloud, AI, etc.) "
            "and evaluating their relevance to the business. Define a clear path from idea "
            "to proof of concept to production. Ensure innovation investments are tracked "
            "and evaluated. Avoid chasing technology for its own sake — link every innovation "
            "initiative to a business problem or opportunity."
        ),
        testing_procedure=(
            "1. Obtain evidence of technology trend monitoring (reports, subscriptions, working groups). "
            "2. Review the innovation pipeline or register of initiatives being evaluated. "
            "3. Confirm there is a defined process for evaluating and approving innovation pilots. "
            "4. Select a sample of completed innovation projects and verify outcomes were assessed. "
            "5. Check that innovation initiatives are linked to business objectives."
        ),
        control_type=ControlType.PREVENTIVE,
        automation_level=AutomationLevel.MANUAL,
        aliases=["technology innovation", "emerging technology", "innovation management"],
    ))

    controls.append(Control(
        framework_id=framework_id,
        domain_id=apo.id,
        control_id_code="APO05",
        title="Managed Portfolio",
        description=(
            "Execute the strategic direction for investments and make investment and service "
            "decisions that maximise the value delivered from the IT portfolio. Balance the "
            "portfolio considering risk."
        ),
        objective=(
            "Optimise the performance of the overall portfolio of IT programmes, projects "
            "and services in relation to enterprise objectives. Ensure IT investments are "
            "prioritised against strategic benefit and risk."
        ),
        guidance=(
            "Maintain a consolidated view of all IT investments (projects, programmes, "
            "ongoing services). Use a formal prioritisation process — not first come, first "
            "served. Evaluate investments on business value, cost, risk and strategic fit. "
            "Review the portfolio regularly and rebalance as priorities change. Kill or pause "
            "projects that are no longer delivering value — this is harder but important."
        ),
        testing_procedure=(
            "1. Obtain the IT portfolio or project inventory for the current year. "
            "2. Verify a formal prioritisation process exists and is documented. "
            "3. Review investment approval records — confirm approvals followed the process. "
            "4. Check portfolio review meeting minutes for evidence of active oversight. "
            "5. Confirm that cancelled or paused projects were formally reviewed, not just abandoned."
        ),
        control_type=ControlType.PREVENTIVE,
        automation_level=AutomationLevel.MANUAL,
        aliases=["IT portfolio management", "investment management", "project portfolio"],
    ))

    controls.append(Control(
        framework_id=framework_id,
        domain_id=apo.id,
        control_id_code="APO06",
        title="Managed Budget and Costs",
        description=(
            "Manage the financial activities related to IT, covering the budget, cost and "
            "benefit management, and prioritisation of spending through the use of formal "
            "budgeting practices and a fair and equitable system for distributing costs to "
            "the business."
        ),
        objective=(
            "Foster partnership between IT and business stakeholders to enable the effective "
            "and efficient use of IT resources and provide transparency of IT costs, benefits "
            "and risks. Enable the enterprise to make informed decisions regarding IT spending."
        ),
        guidance=(
            "Maintain a clear IT budget that is approved annually and tracked monthly. Costs "
            "should be allocated to business units in a transparent and understandable way. "
            "Explain what each IT cost buys — business units should know what they are paying "
            "for. Track actuals against budget and explain variances. In banking, regulators "
            "expect clear cost attribution between business lines."
        ),
        testing_procedure=(
            "1. Obtain the approved IT budget for the current year. "
            "2. Review monthly IT financial reports and confirm variances are explained. "
            "3. Verify cost allocation methodology is documented and applied consistently. "
            "4. Check that IT budget approval followed the governance process. "
            "5. Confirm IT finance reporting is presented to the appropriate oversight body."
        ),
        control_type=ControlType.DETECTIVE,
        automation_level=AutomationLevel.SEMI_AUTO,
        aliases=["IT budget", "IT financial management", "IT cost management"],
    ))

    controls.append(Control(
        framework_id=framework_id,
        domain_id=apo.id,
        control_id_code="APO07",
        title="Managed Human Resources",
        description=(
            "Provide a structured approach to ensure optimal structuring, placement, decision "
            "rights and skills of human resources. This includes communicating defined roles "
            "and responsibilities, learning and growth plans, and performance expectations, "
            "supported with competent and motivated people."
        ),
        objective=(
            "Optimise human resource capabilities to meet enterprise objectives. Ensure IT "
            "staff have the skills needed, are properly onboarded and offboarded, and that "
            "key person dependencies are managed."
        ),
        guidance=(
            "Maintain an IT skills framework — what competencies does each role need? Conduct "
            "regular skills gap analysis and act on the results. Ensure leavers have access "
            "promptly revoked (this is also a security control). Manage key person risk — "
            "critical knowledge should not exist in one person's head. In banking, regulators "
            "scrutinise IT staffing heavily."
        ),
        testing_procedure=(
            "1. Verify all IT staff have documented roles with clear responsibilities. "
            "2. Review the skills assessment process and confirm it was conducted recently. "
            "3. Sample 5-10 staff departures: confirm system access was revoked within "
            "the required timeframe. "
            "4. Check for documented succession plans for critical IT roles. "
            "5. Confirm training and development plans exist for IT staff."
        ),
        control_type=ControlType.PREVENTIVE,
        automation_level=AutomationLevel.MANUAL,
        aliases=["IT HR management", "IT staffing", "IT workforce management"],
    ))

    controls.append(Control(
        framework_id=framework_id,
        domain_id=apo.id,
        control_id_code="APO08",
        title="Managed Relationships",
        description=(
            "Manage the relationship between IT and business in a formalised and transparent "
            "way that ensures focus on achieving a common and shared goal of successful "
            "enterprise outcomes."
        ),
        objective=(
            "Create and maintain a positive and constructive relationship between IT and "
            "business stakeholders. Ensure business priorities are understood by IT. "
            "Ensure IT capabilities are understood by the business."
        ),
        guidance=(
            "Establish formal relationship management mechanisms — typically IT steering "
            "committees, business relationship managers, and regular business reviews. "
            "These meetings should have agendas, minutes, and actions. Relationship "
            "management prevents the classic IT-business disconnect where IT builds what "
            "they think the business wants, rather than what it actually needs."
        ),
        testing_procedure=(
            "1. Obtain evidence of IT steering committee or equivalent meetings (agenda, minutes). "
            "2. Verify meetings are held at the documented frequency. "
            "3. Check that actions from previous meetings are tracked and followed up. "
            "4. Confirm business relationship managers or equivalents are in place for key units. "
            "5. Review evidence of IT satisfaction surveys or feedback mechanisms."
        ),
        control_type=ControlType.PREVENTIVE,
        automation_level=AutomationLevel.MANUAL,
        aliases=["IT business alignment", "business relationship management", "IT steering committee"],
    ))

    controls.append(Control(
        framework_id=framework_id,
        domain_id=apo.id,
        control_id_code="APO09",
        title="Managed Service Agreements",
        description=(
            "Align IT-enabled services and service levels with enterprise needs and expectations, "
            "including identification, specification, design, publishing, agreement and monitoring "
            "of IT services, service levels and performance indicators."
        ),
        objective=(
            "Ensure IT services are defined and agreed upon with the business. Ensure service "
            "levels are monitored and reported. Ensure service failures are managed and "
            "remediated."
        ),
        guidance=(
            "Maintain a service catalogue that describes each IT service in plain English. "
            "For critical services, document formal SLAs including availability targets, "
            "response times, and support hours. Track actual service performance against SLAs "
            "monthly. Report to business stakeholders. In banking, core systems need SLAs "
            "tied to regulatory availability requirements."
        ),
        testing_procedure=(
            "1. Obtain the IT service catalogue and confirm it is current and communicated. "
            "2. Review SLAs for critical services — confirm availability and response targets are defined. "
            "3. Obtain service performance reports for the past quarter and compare to SLA targets. "
            "4. Check how SLA breaches are managed — is there a formal process? "
            "5. Confirm SLAs are reviewed at least annually with business stakeholders."
        ),
        control_type=ControlType.DETECTIVE,
        automation_level=AutomationLevel.SEMI_AUTO,
        aliases=["SLA management", "service catalogue", "service level management"],
    ))

    controls.append(Control(
        framework_id=framework_id,
        domain_id=apo.id,
        control_id_code="APO10",
        title="Managed Vendors",
        description=(
            "Manage IT-related services provided by all types of vendors to meet enterprise "
            "requirements, including selection of vendors, management of relationships, "
            "management of contracts and reviewing and monitoring vendor performance and risk."
        ),
        objective=(
            "Minimise the risk associated with non-performing or failing IT vendors. Ensure "
            "IT vendors meet their contractual obligations. Ensure vendor dependencies and "
            "concentration risks are understood and managed."
        ),
        guidance=(
            "Maintain a vendor register for all significant IT suppliers. Conduct due diligence "
            "before onboarding new vendors. Ensure contracts include performance SLAs, data "
            "protection clauses, audit rights, and exit provisions. Monitor vendor performance "
            "regularly. For critical vendors, conduct formal annual reviews. In banking, third "
            "party and vendor risk management is heavily regulated (OCC Bulletin 2013-29, "
            "FFIEC guidance). Concentration risk across vendors is a key examiner focus."
        ),
        testing_procedure=(
            "1. Obtain the vendor register and confirm it is complete and current. "
            "2. Sample 3-5 critical vendors: verify contracts exist with SLAs and audit rights. "
            "3. Review vendor performance reports for sampled vendors — are SLAs being met? "
            "4. Check vendor due diligence records — was financial/security due diligence performed? "
            "5. Confirm an exit plan exists for at least the most critical vendor relationships. "
            "6. Verify vendor concentration risk is assessed and documented."
        ),
        control_type=ControlType.PREVENTIVE,
        automation_level=AutomationLevel.MANUAL,
        aliases=["vendor management", "third party risk", "supplier management", "outsourcing management"],
    ))

    controls.append(Control(
        framework_id=framework_id,
        domain_id=apo.id,
        control_id_code="APO11",
        title="Managed Quality",
        description=(
            "Define and communicate quality requirements in all processes, procedures and "
            "related enterprise outcomes. Use quality management practices to ensure delivery "
            "of products, services and solutions."
        ),
        objective=(
            "Ensure that IT processes and deliverables meet agreed quality standards. "
            "Identify and track quality defects. Continuously improve IT processes."
        ),
        guidance=(
            "Establish a quality management framework for IT — this doesn't need to be "
            "ISO 9001 certified, but there should be defined standards, review processes, "
            "and a mechanism for capturing and learning from defects. Conduct regular "
            "process reviews. For software, this means code review, testing standards, "
            "and defect tracking. In banking, quality in critical systems is a safety "
            "and soundness matter."
        ),
        testing_procedure=(
            "1. Obtain the IT quality management policy or framework document. "
            "2. Review quality metrics reports — are defect rates, rework rates, etc. tracked? "
            "3. Confirm quality reviews are conducted for significant IT deliverables. "
            "4. Check that quality issues are logged, tracked and resolved. "
            "5. Verify process improvement activities are documented and followed up."
        ),
        control_type=ControlType.DETECTIVE,
        automation_level=AutomationLevel.SEMI_AUTO,
        aliases=["IT quality management", "quality assurance", "QA"],
    ))

    controls.append(Control(
        framework_id=framework_id,
        domain_id=apo.id,
        control_id_code="APO12",
        title="Managed Risk",
        description=(
            "Continually identify, assess and reduce IT-related risks within levels of "
            "tolerance set by enterprise executive management. Integrate the management of "
            "IT-related enterprise risk with overall ERM."
        ),
        objective=(
            "Integrate IT risk management into the enterprise risk management framework. "
            "Ensure IT risks are identified, assessed, treated and monitored. Ensure risk "
            "information is communicated to decision makers in a timely and accurate way."
        ),
        guidance=(
            "Maintain a current IT risk register. Every significant IT risk should have: "
            "a risk owner, a risk rating (inherent and residual), a treatment plan, and a "
            "review date. Risk assessments should be refreshed when new threats emerge or "
            "the environment changes materially. Report IT risk to the board risk committee "
            "regularly. In banking, risk management is a regulatory requirement — examiners "
            "will look at the IT risk register directly."
        ),
        testing_procedure=(
            "1. Obtain the IT risk register and confirm it is current (reviewed within 6-12 months). "
            "2. Verify every risk has an owner, inherent rating, residual rating, and treatment plan. "
            "3. Sample 5 risks and check that treatment plans have been actioned. "
            "4. Confirm the risk register was presented to the board or risk committee recently. "
            "5. Check that new/emerging risks are being added (not just old ones recycled)."
        ),
        control_type=ControlType.DETECTIVE,
        automation_level=AutomationLevel.MANUAL,
        aliases=["IT risk management", "risk register", "risk assessment", "ERM IT"],
    ))

    controls.append(Control(
        framework_id=framework_id,
        domain_id=apo.id,
        control_id_code="APO13",
        title="Managed Security",
        description=(
            "Define, operate and monitor a system for information security management. "
            "Establish and maintain information security roles and responsibilities, "
            "policies, standards and procedures."
        ),
        objective=(
            "Keep the impact of information security incidents within the enterprise's "
            "risk appetite. Protect information and supporting assets from unauthorised "
            "access, use, disclosure, modification, destruction or interference."
        ),
        guidance=(
            "This is the COBIT equivalent of an information security management system "
            "(comparable to ISO 27001). Establish a security policy, define security "
            "roles (e.g., CISO), conduct risk assessments, and implement a security "
            "control framework. For banking, this must align with FFIEC security guidance. "
            "Treat APO13 as the parent control — the specific technical controls sit "
            "under DSS05 (Managed Security Services)."
        ),
        testing_procedure=(
            "1. Obtain the information security policy and confirm it is board-approved and current. "
            "2. Verify information security roles are defined (CISO or equivalent). "
            "3. Review the information security risk assessment — confirm it covers key assets. "
            "4. Check that security awareness training is in place and completion is tracked. "
            "5. Confirm the security programme has an annual review cycle."
        ),
        control_type=ControlType.PREVENTIVE,
        automation_level=AutomationLevel.MANUAL,
        aliases=["information security management", "ISMS", "security programme", "infosec management"],
    ))

    controls.append(Control(
        framework_id=framework_id,
        domain_id=apo.id,
        control_id_code="APO14",
        title="Managed Data",
        description=(
            "Manage enterprise data as a strategic asset. Establish, maintain and use "
            "a data management system for making accurate and complete data available "
            "to support all relevant governance, management and business processes."
        ),
        objective=(
            "Ensure the quality, integrity and security of enterprise data. Ensure data "
            "is available to decision makers when needed. Ensure compliance with data "
            "protection and privacy regulations."
        ),
        guidance=(
            "APO14 was added in COBIT 2019 in recognition that data is a critical enterprise "
            "asset. Establish data ownership (who is responsible for each major data asset), "
            "data quality standards, data classification, and data retention policies. "
            "In banking this connects directly to data governance, BCBS 239 (risk data "
            "aggregation), and customer data protection under relevant privacy laws."
        ),
        testing_procedure=(
            "1. Obtain the data governance policy and confirm data owners are assigned. "
            "2. Verify a data classification scheme exists and is applied to key data assets. "
            "3. Check data quality metrics are tracked for critical data sets. "
            "4. Confirm data retention and disposal policies are documented and enforced. "
            "5. Review data protection impact assessments for new data-heavy projects."
        ),
        control_type=ControlType.PREVENTIVE,
        automation_level=AutomationLevel.SEMI_AUTO,
        aliases=["data governance", "data management", "BCBS 239", "data quality"],
    ))

    # ================================================================
    # BAI DOMAIN — 11 management objectives
    # ================================================================

    controls.append(Control(
        framework_id=framework_id,
        domain_id=bai.id,
        control_id_code="BAI01",
        title="Managed Programs",
        description=(
            "Manage all programmes in the investment portfolio in alignment with the "
            "enterprise strategy and in a coordinated way. Initiate, plan, control and "
            "execute programmes, and monitor the portfolio of programmes."
        ),
        objective=(
            "Realise business benefits and reduce the risk of unexpected delays, costs and "
            "quality issues. Ensure programmes are aligned to strategy and delivered "
            "within agreed scope, time and budget."
        ),
        guidance=(
            "Programmes are collections of related projects delivering a strategic change "
            "(e.g., a core banking replacement). Programme management requires a programme "
            "manager, a programme board, a benefits case, and formal governance milestones. "
            "Distinguish clearly between projects (BAI11) and programmes (BAI01). Large "
            "banking technology programmes routinely exceed budget and schedule — strong "
            "programme governance is how you prevent this."
        ),
        testing_procedure=(
            "1. Select the current major IT programme(s) for review. "
            "2. Verify a programme business case was approved before initiation. "
            "3. Confirm a programme manager is assigned and a programme board meets regularly. "
            "4. Review programme status reports — are scope, budget and timeline being tracked? "
            "5. Check that benefits realisation is tracked post-delivery."
        ),
        control_type=ControlType.PREVENTIVE,
        automation_level=AutomationLevel.MANUAL,
        aliases=["programme management", "program management", "IT programme governance"],
    ))

    controls.append(Control(
        framework_id=framework_id,
        domain_id=bai.id,
        control_id_code="BAI02",
        title="Managed Requirements Definition",
        description=(
            "Identify solutions and analyse requirements before acquisition or creation "
            "to ensure they are in line with enterprise strategic requirements and that "
            "the business processes, applications, information/data, infrastructure and "
            "services are aligned."
        ),
        objective=(
            "Create feasible optimal solutions that meet the enterprise's strategic, "
            "operational and technology needs while minimising risk. Ensure requirements "
            "are clearly defined before building or buying."
        ),
        guidance=(
            "Before starting any IT development or procurement, document requirements "
            "formally and get business sign-off. Poor requirements are the single biggest "
            "cause of IT project failure. Include functional requirements (what it must do), "
            "non-functional requirements (performance, security, availability), and "
            "regulatory requirements. In banking, missing regulatory requirements in "
            "system specs is a common audit finding."
        ),
        testing_procedure=(
            "1. Select a sample of recently completed IT projects. "
            "2. For each, verify a requirements document was produced and signed off by business. "
            "3. Check that requirements included security, privacy and regulatory considerations. "
            "4. Review change requests — were scope changes formally approved? "
            "5. Confirm post-implementation testing validated that requirements were met."
        ),
        control_type=ControlType.PREVENTIVE,
        automation_level=AutomationLevel.MANUAL,
        aliases=["requirements management", "business requirements", "system requirements"],
    ))

    controls.append(Control(
        framework_id=framework_id,
        domain_id=bai.id,
        control_id_code="BAI03",
        title="Managed Solutions Identification and Build",
        description=(
            "Establish and maintain identified solutions in line with enterprise requirements "
            "covering design, development, procurement/sourcing and partnering with suppliers "
            "and vendors. Manage configuration, test preparation, testing, requirements "
            "management and maintenance of business processes, applications, information "
            "and technology solutions."
        ),
        objective=(
            "Establish timely and cost-effective solutions capable of supporting enterprise "
            "strategic and operational objectives. Ensure solutions are secure, fit for "
            "purpose and align to the architecture."
        ),
        guidance=(
            "Implement a structured SDLC (software development lifecycle) or equivalent "
            "procurement process. This should cover: design review, code review, security "
            "testing (SAST/DAST), user acceptance testing, and sign-off before go-live. "
            "In banking, regulators expect evidence of testing, especially for changes to "
            "systems that handle customer money or regulatory reporting."
        ),
        testing_procedure=(
            "1. Select a sample of recent IT solutions delivered (build or buy). "
            "2. Verify design documentation exists and was reviewed. "
            "3. Confirm security requirements were built into the design (not bolted on after). "
            "4. Check test results — was UAT conducted? Were defects tracked and resolved? "
            "5. Verify formal sign-off was obtained before the solution went live."
        ),
        control_type=ControlType.PREVENTIVE,
        automation_level=AutomationLevel.SEMI_AUTO,
        aliases=["SDLC", "software development", "solution design", "build and buy"],
    ))

    controls.append(Control(
        framework_id=framework_id,
        domain_id=bai.id,
        control_id_code="BAI04",
        title="Managed Availability and Capacity",
        description=(
            "Balance current and future needs for availability, performance and capacity "
            "with cost-effective service provision. Include assessment of current capabilities, "
            "forecasting of future needs based on business requirements, and analysis of "
            "business impacts."
        ),
        objective=(
            "Maintain service availability, efficient management of resources and "
            "optimisation of system performance through prediction of future performance "
            "and capacity requirements."
        ),
        guidance=(
            "Maintain a capacity plan that projects future IT resource needs (compute, "
            "storage, network, people) based on business growth forecasts. Monitor actual "
            "utilisation against thresholds — don't wait until systems are at 90% capacity "
            "to act. In banking, availability targets for payment systems and core banking "
            "are often set by regulation. Capacity failures can cause service outages with "
            "regulatory and reputational consequences."
        ),
        testing_procedure=(
            "1. Obtain the IT capacity plan and confirm it covers compute, storage and network. "
            "2. Review capacity utilisation reports for the past quarter — are any resources near limits? "
            "3. Confirm availability targets are defined for critical systems. "
            "4. Review availability reports and confirm targets are being met. "
            "5. Check that capacity planning feeds into the annual IT budget process."
        ),
        control_type=ControlType.PREVENTIVE,
        automation_level=AutomationLevel.SEMI_AUTO,
        aliases=["capacity management", "availability management", "performance management"],
    ))

    controls.append(Control(
        framework_id=framework_id,
        domain_id=bai.id,
        control_id_code="BAI05",
        title="Managed Organisational Change",
        description=(
            "Maximise the likelihood of successfully implementing organisation-wide change "
            "quickly and with reduced risk by covering the complete life cycle of the change "
            "and all affected stakeholders."
        ),
        objective=(
            "Prepare and commit stakeholders for business change and reduce the risk of "
            "failure. Ensure people understand and accept IT-enabled changes to the way "
            "they work."
        ),
        guidance=(
            "This is change management from a people/organisation perspective — not IT "
            "system changes (that's BAI06). When implementing new IT systems, the technology "
            "is often the easy part; getting people to adopt and use it correctly is harder. "
            "Assign a change manager for significant implementations, develop training and "
            "communication plans, and measure adoption after go-live. Failed adoption is a "
            "major cause of IT investment write-offs."
        ),
        testing_procedure=(
            "1. Select a major IT implementation from the past 12-24 months. "
            "2. Review the change management plan — was stakeholder impact analysed? "
            "3. Confirm training was delivered before go-live. "
            "4. Check post-implementation adoption metrics or user satisfaction surveys. "
            "5. Verify communications were sent to all affected parties before and during rollout."
        ),
        control_type=ControlType.PREVENTIVE,
        automation_level=AutomationLevel.MANUAL,
        aliases=["organisational change management", "OCM", "change adoption", "business change"],
    ))

    controls.append(Control(
        framework_id=framework_id,
        domain_id=bai.id,
        control_id_code="BAI06",
        title="Managed IT Changes",
        description=(
            "Manage all changes to IT infrastructure and applications in a controlled manner, "
            "including standard changes, maintenance patches, emergency changes and significant "
            "changes, ensuring minimisation of risk and impact of change on IT systems."
        ),
        objective=(
            "Enable fast and reliable delivery of change to the business, while mitigating "
            "the risk of negatively impacting the stability of the changed environment."
        ),
        guidance=(
            "Implement a formal change management process: all changes must be logged, "
            "assessed for risk/impact, approved by the Change Advisory Board (CAB), "
            "scheduled to minimise disruption, tested, and documented. Emergency changes "
            "should follow an expedited process but must still be approved retrospectively "
            "and documented. In banking, poorly controlled changes are a top cause of "
            "system outages and audit findings. The CAB must be genuinely independent — "
            "not just a rubber stamp for developers."
        ),
        testing_procedure=(
            "1. Obtain the change management policy and confirm all change types are covered. "
            "2. Sample 20-30 changes from the change register — verify each followed the process. "
            "3. Confirm CAB meetings are held and attended by appropriate stakeholders. "
            "4. Review emergency changes — were they approved retrospectively and root-caused? "
            "5. Check that unauthorised changes are detected (via config monitoring or post-facto review). "
            "6. Verify change success rates are tracked and failures are post-implementation reviewed."
        ),
        control_type=ControlType.PREVENTIVE,
        automation_level=AutomationLevel.SEMI_AUTO,
        aliases=["change management", "change control", "ITIL change", "CAB"],
    ))

    controls.append(Control(
        framework_id=framework_id,
        domain_id=bai.id,
        control_id_code="BAI07",
        title="Managed IT Change Acceptance and Transitioning",
        description=(
            "Formally accept and make operational new solutions, including implementation "
            "planning, system and data conversion, acceptance testing, communication, "
            "release preparation, promotion to production and post-implementation review."
        ),
        objective=(
            "Implement solutions safely and in line with the agreed expectations and "
            "outcomes. Ensure that the transition to production is controlled and that "
            "there is a rollback plan if the release fails."
        ),
        guidance=(
            "This control focuses on the go-live transition — different from change management "
            "(BAI06) which is about the process, and solution build (BAI03) which is about "
            "what was built. Key elements: a documented release plan, a rollback plan, "
            "a cutover checklist, go/no-go criteria, and a post-implementation review. "
            "In banking, releases to core systems often require regulator notification or "
            "pre-notification to customers."
        ),
        testing_procedure=(
            "1. Select 3-5 significant releases from the past 12 months. "
            "2. For each: verify a release plan and rollback plan existed. "
            "3. Check that go/no-go criteria were formally assessed before cutover. "
            "4. Confirm post-implementation reviews were conducted and issues captured. "
            "5. Verify data migration (if applicable) was validated for accuracy and completeness."
        ),
        control_type=ControlType.PREVENTIVE,
        automation_level=AutomationLevel.SEMI_AUTO,
        aliases=["release management", "deployment management", "go-live", "cutover"],
    ))

    controls.append(Control(
        framework_id=framework_id,
        domain_id=bai.id,
        control_id_code="BAI08",
        title="Managed Knowledge",
        description=(
            "Maintain the availability of relevant, current, validated and reliable knowledge "
            "to support all process activities and facilitate decision making."
        ),
        objective=(
            "Ensure that knowledge needed to support IT activities is documented and accessible. "
            "Prevent knowledge loss through staff departures. Enable consistent execution "
            "of IT processes."
        ),
        guidance=(
            "Knowledge management in IT means ensuring critical knowledge is captured "
            "and not just in people's heads. This includes: documentation of key systems "
            "and processes, lessons learned from projects and incidents, IT runbooks, "
            "and knowledge bases for support staff. In banking, key person risk — where "
            "one person holds all the knowledge about a critical system — is a regulatory "
            "and operational concern."
        ),
        testing_procedure=(
            "1. Identify 3-5 critical IT systems and check whether current documentation exists. "
            "2. Verify a process exists for capturing lessons learned from projects and incidents. "
            "3. Assess whether documentation is accessible and kept up to date. "
            "4. Identify key person risks — are any critical systems documented by only one person? "
            "5. Check that new staff can access the knowledge they need to perform their roles."
        ),
        control_type=ControlType.PREVENTIVE,
        automation_level=AutomationLevel.MANUAL,
        aliases=["knowledge management", "documentation management", "IT runbooks"],
    ))

    controls.append(Control(
        framework_id=framework_id,
        domain_id=bai.id,
        control_id_code="BAI09",
        title="Managed Assets",
        description=(
            "Manage IT assets through their lifecycle to make sure that their use delivers "
            "value at optimal cost, they remain in use for as long as they justify investment, "
            "and they are accounted for and physically protected."
        ),
        objective=(
            "Account for all IT assets and optimise the value provided by assets. Ensure "
            "assets are tracked from acquisition to disposal. Ensure disposed assets do not "
            "create data leakage risks."
        ),
        guidance=(
            "Maintain an IT asset register covering hardware, software licences, cloud "
            "subscriptions, and data assets. Each asset should have an owner. Track "
            "asset lifecycle — acquisition, maintenance, refresh, disposal. Software "
            "licence compliance is a significant financial risk (audits by vendors). "
            "Data destruction at end-of-life is critical — in banking, customer data "
            "on decommissioned hardware is a serious compliance risk."
        ),
        testing_procedure=(
            "1. Obtain the IT asset register and verify it was reconciled within the past year. "
            "2. Perform a physical spot-check of hardware assets against the register. "
            "3. Review software licence management — confirm licences are not over or under-used. "
            "4. Sample recent hardware disposals: verify data was destroyed to an approved standard. "
            "5. Confirm asset owners are assigned for all significant assets."
        ),
        control_type=ControlType.PREVENTIVE,
        automation_level=AutomationLevel.SEMI_AUTO,
        aliases=["asset management", "IT asset register", "CMDB", "hardware management"],
    ))

    controls.append(Control(
        framework_id=framework_id,
        domain_id=bai.id,
        control_id_code="BAI10",
        title="Managed Configuration",
        description=(
            "Define and maintain descriptions and relationships between key resources and "
            "capabilities required to deliver IT-enabled services, including collecting "
            "configuration information, establishing baselines, verifying and auditing "
            "configuration information and updating the configuration repository."
        ),
        objective=(
            "Provide sufficient information about service assets to enable the service "
            "to be effectively managed. Assess the impact of changes and deal with service "
            "incidents more effectively."
        ),
        guidance=(
            "Maintain a configuration management database (CMDB) that records the "
            "configuration of key IT components (servers, network devices, applications, "
            "databases). Baselines should be set for secure configurations and changes "
            "to configs should be tracked. The CMDB supports change management (BAI06), "
            "incident management (DSS02) and security (DSS05). In banking, configuration "
            "drift — systems gradually deviating from their secure baseline — is a key "
            "security and resilience risk."
        ),
        testing_procedure=(
            "1. Verify a CMDB or equivalent configuration repository exists. "
            "2. Confirm configuration baselines are defined for key system types. "
            "3. Sample 5-10 critical systems: compare actual config to documented baseline. "
            "4. Check that configuration changes are linked to approved change requests. "
            "5. Review how frequently the CMDB is reconciled against actual environments."
        ),
        control_type=ControlType.DETECTIVE,
        automation_level=AutomationLevel.SEMI_AUTO,
        aliases=["configuration management", "CMDB", "baseline management", "config drift"],
    ))

    controls.append(Control(
        framework_id=framework_id,
        domain_id=bai.id,
        control_id_code="BAI11",
        title="Managed Projects",
        description=(
            "Initiate, plan, control and execute projects in alignment with the programme "
            "and within the portfolio. Manage project scope, schedule, quality, costs and "
            "risk, and ensure that IT projects contribute to programme and portfolio results."
        ),
        objective=(
            "Realise project outcomes and reduce the risk of unexpected delays, costs "
            "and quality shortfalls. Deliver IT projects within agreed scope, time and budget."
        ),
        guidance=(
            "Every significant IT change should be run as a formal project with: a project "
            "charter (scope, budget, timeline), a project manager, a project plan, regular "
            "status reporting, and a formal closure with lessons learned. The project size "
            "should determine the level of governance applied — a $50K project doesn't need "
            "the same overhead as a $5M one. In banking, IT projects that touch regulatory "
            "systems should always be formally managed."
        ),
        testing_procedure=(
            "1. Obtain the project register for the current year. "
            "2. Select a sample of 3-5 completed or in-flight projects. "
            "3. For each: verify a project charter/plan exists with scope, budget, timeline. "
            "4. Review project status reports — were risks and issues tracked? "
            "5. For completed projects: confirm formal closure and lessons learned were documented."
        ),
        control_type=ControlType.PREVENTIVE,
        automation_level=AutomationLevel.MANUAL,
        aliases=["project management", "IT project governance", "PMO"],
    ))

    # ================================================================
    # DSS DOMAIN — 6 management objectives
    # ================================================================

    controls.append(Control(
        framework_id=framework_id,
        domain_id=dss.id,
        control_id_code="DSS01",
        title="Managed Operations",
        description=(
            "Coordinate and execute the activities and operational procedures required "
            "to deliver internal and outsourced IT services, including the execution of "
            "predefined standard operating procedures and the required monitoring activities."
        ),
        objective=(
            "Deliver IT operational services as expected, in an efficient and reliable "
            "manner. Ensure that the IT operational environment is stable and well-managed."
        ),
        guidance=(
            "Define standard operating procedures (SOPs) for all significant IT operational "
            "activities: job scheduling, backup and recovery, system monitoring, batch "
            "processing, data centre operations. Ensure operations staff follow procedures "
            "and that deviations are documented. Monitor key operational metrics. In banking, "
            "uncontrolled batch processes and poor job scheduling are classic audit findings."
        ),
        testing_procedure=(
            "1. Obtain the set of IT operational SOPs and confirm they are current. "
            "2. Verify critical operational tasks (backups, batch jobs) are scheduled and monitored. "
            "3. Review operational job logs — confirm scheduled jobs ran successfully or failures were addressed. "
            "4. Check that operational procedures are followed — interview operations staff. "
            "5. Confirm a process exists for handling operational exceptions and escalating failures."
        ),
        control_type=ControlType.PREVENTIVE,
        automation_level=AutomationLevel.SEMI_AUTO,
        aliases=["IT operations", "operations management", "IT ops", "batch management"],
    ))

    controls.append(Control(
        framework_id=framework_id,
        domain_id=dss.id,
        control_id_code="DSS02",
        title="Managed Service Requests and Incidents",
        description=(
            "Provide timely and effective response to user requests and resolution of all "
            "types of incidents. Restore normal service; record and fulfil user requests; "
            "and record, investigate, diagnose, escalate and resolve incidents."
        ),
        objective=(
            "Achieve increased productivity and minimise disruptions through quick resolution "
            "of user queries and incidents. Restore normal IT service operation as quickly "
            "as possible."
        ),
        guidance=(
            "Operate a formal IT service desk (or equivalent) with a ticketing system. "
            "Define and meet service response and resolution SLAs (e.g., Priority 1 incidents "
            "acknowledged within 15 minutes, resolved within 4 hours). Classify incidents by "
            "priority based on impact and urgency. Escalate major incidents to management. "
            "In banking, payment system incidents may require immediate escalation to the "
            "CISO, CTO and potentially regulators depending on severity."
        ),
        testing_procedure=(
            "1. Obtain incident response metrics (volume, resolution times, SLA performance). "
            "2. Confirm incident priority categories and SLAs are defined. "
            "3. Sample 10-15 incidents: verify they were logged, classified, resolved and closed properly. "
            "4. Review major incidents: were they escalated appropriately and post-incident reviewed? "
            "5. Check that incident trends are analysed and fed into problem management (DSS03)."
        ),
        control_type=ControlType.DETECTIVE,
        automation_level=AutomationLevel.SEMI_AUTO,
        aliases=["incident management", "service desk", "helpdesk", "ITIL incident"],
    ))

    controls.append(Control(
        framework_id=framework_id,
        domain_id=dss.id,
        control_id_code="DSS03",
        title="Managed Problems",
        description=(
            "Identify and classify problems and their root causes and provide timely "
            "resolution to prevent recurring incidents. Provide recommendations for improvements."
        ),
        objective=(
            "Increase availability, improve service levels, reduce costs and improve "
            "customer convenience and satisfaction by reducing the number of operational "
            "problems and finding root causes of all significant incidents."
        ),
        guidance=(
            "Problem management is the process of finding the root cause of recurring "
            "incidents and fixing them permanently — as opposed to incident management "
            "which just restores service. Identify known errors (diagnosed but not yet "
            "fixed) and track their resolution. Conduct formal root cause analysis (RCA) "
            "for major incidents. In banking, the same system failing repeatedly without "
            "root cause analysis is a significant audit finding."
        ),
        testing_procedure=(
            "1. Obtain the problem register and confirm it is current and actively maintained. "
            "2. Verify root cause analysis was conducted for all major incidents in the past year. "
            "3. Sample 5 problems: confirm root causes are identified and remediation plans exist. "
            "4. Check that known errors are documented and disclosed to support teams. "
            "5. Confirm problem trends are reported to IT management."
        ),
        control_type=ControlType.CORRECTIVE,
        automation_level=AutomationLevel.MANUAL,
        aliases=["problem management", "root cause analysis", "RCA", "ITIL problem"],
    ))

    controls.append(Control(
        framework_id=framework_id,
        domain_id=dss.id,
        control_id_code="DSS04",
        title="Managed Continuity",
        description=(
            "Establish and maintain a plan to enable the business and IT to respond to "
            "incidents and disruptions in order to continue operation of critical business "
            "processes and required IT services and maintain availability of information "
            "at a level acceptable to the enterprise."
        ),
        objective=(
            "Continue critical business operations and maintain availability of information "
            "at a level acceptable to the enterprise in the event of a significant disruption. "
            "Provide the ability to recover from major IT failures."
        ),
        guidance=(
            "Implement a Business Continuity Plan (BCP) and IT Disaster Recovery Plan (DRP). "
            "These are not the same thing — BCP covers how the business operates during "
            "disruption; DRP covers how IT systems are recovered. For banking, regulators "
            "mandate BCP/DR testing at least annually. Recovery Time Objectives (RTOs) and "
            "Recovery Point Objectives (RPOs) must be defined and tested. A plan that exists "
            "but has never been tested is not a control — it's a hope."
        ),
        testing_procedure=(
            "1. Obtain the BCP and DRP documents and confirm they are current. "
            "2. Verify RTOs and RPOs are defined for all critical systems. "
            "3. Obtain evidence of the most recent BCP/DR test — what was tested, what were the results? "
            "4. Confirm identified gaps from the test have remediation plans. "
            "5. Check that BCP/DRP training and awareness is conducted for relevant staff. "
            "6. Verify the plan was reviewed and updated following any significant changes."
        ),
        control_type=ControlType.CORRECTIVE,
        automation_level=AutomationLevel.SEMI_AUTO,
        aliases=["business continuity", "disaster recovery", "BCP", "DRP", "BCM"],
    ))

    controls.append(Control(
        framework_id=framework_id,
        domain_id=dss.id,
        control_id_code="DSS05",
        title="Managed Security Services",
        description=(
            "Protect enterprise information to maintain the level of information security "
            "risk acceptable to the enterprise. Establish and maintain information security "
            "roles and responsibilities, policies, standards and procedures."
        ),
        objective=(
            "Minimise the impact of operational information security vulnerabilities and "
            "incidents. Protect all IT assets to minimise the risk of unauthorised access, "
            "use, disclosure, modification, destruction or interference."
        ),
        guidance=(
            "DSS05 is the operational security layer — where APO13 sets the strategy, "
            "DSS05 executes it. Key activities: access management (who can access what), "
            "endpoint protection, network security, vulnerability management, security "
            "monitoring and logging. In banking, examiner focus areas: privileged access "
            "management (PAM), patch management timeliness, network segmentation, and "
            "security logging/SIEM. Access reviews are a top finding area — generic accounts, "
            "orphaned accounts, and excessive privileges."
        ),
        testing_procedure=(
            "1. Verify logical access controls: review user access provisioning/de-provisioning processes. "
            "2. Sample 10-15 user accounts on critical systems: confirm access is appropriate for role. "
            "3. Check privileged access management: admin accounts should be inventoried and controlled. "
            "4. Review patch management reports: how current are patches on critical systems? "
            "5. Confirm security monitoring/logging is in place and reviewed. "
            "6. Verify vulnerability scanning is performed regularly and findings remediated within SLAs."
        ),
        control_type=ControlType.PREVENTIVE,
        automation_level=AutomationLevel.SEMI_AUTO,
        aliases=["security services", "access management", "vulnerability management", "security operations", "SOC"],
    ))

    controls.append(Control(
        framework_id=framework_id,
        domain_id=dss.id,
        control_id_code="DSS06",
        title="Managed Business Process Controls",
        description=(
            "Define and maintain appropriate business process controls to ensure that "
            "information related to and processed by in-house or outsourced business "
            "processes satisfies all relevant information control requirements. Identify "
            "the relevant control requirements and manage and operate adequate controls "
            "to ensure that information and information processing satisfy the requirements."
        ),
        objective=(
            "Maintain the integrity of information and information processing. Ensure IT "
            "controls embedded in business processes are appropriate and working. "
            "Support the accuracy and completeness of financial and operational data."
        ),
        guidance=(
            "Business process controls are the IT controls embedded directly in business "
            "processes — input validation, processing controls, output reconciliation, "
            "interface checks, error handling. This is particularly important in banking "
            "where financial transactions flow through multiple systems. For auditors: "
            "automated controls in financial systems are often more reliable than manual "
            "controls, but they still need to be tested. A control that used to work may "
            "have been broken by a system change."
        ),
        testing_procedure=(
            "1. Identify key business processes with embedded IT controls (e.g., payment processing, "
            "GL postings, regulatory reporting). "
            "2. For each critical process: document the key automated controls and test them. "
            "3. Verify input validation controls prevent invalid data from being processed. "
            "4. Check interface and reconciliation controls — confirm data transfers between systems "
            "are validated for completeness and accuracy. "
            "5. Test error handling: what happens when an automated control detects a problem?"
        ),
        control_type=ControlType.DETECTIVE,
        automation_level=AutomationLevel.SEMI_AUTO,
        aliases=["application controls", "automated controls", "business process controls", "IPE controls"],
    ))

    # ================================================================
    # MEA DOMAIN — 4 management objectives
    # ================================================================

    controls.append(Control(
        framework_id=framework_id,
        domain_id=mea.id,
        control_id_code="MEA01",
        title="Managed Performance and Conformance Monitoring",
        description=(
            "Collect, validate and evaluate business, IT and process goals and metrics. "
            "Monitor processes against performance targets and benchmarks and provide "
            "meaningful and timely reporting to management, the board and stakeholders."
        ),
        objective=(
            "Provide transparency of performance and conformance and drive achievement of "
            "goals. Enable management to make informed decisions and take corrective action "
            "where needed."
        ),
        guidance=(
            "Define a balanced set of IT performance metrics (IT scorecard or dashboard). "
            "Include financial, operational, customer-facing, and capability metrics. "
            "Report regularly — monthly to IT management, quarterly to the board. Metrics "
            "should be meaningful to the audience: the board doesn't need to see server "
            "uptime percentages; they need to see business impact. In banking, regulators "
            "expect IT management information to be timely and accurate."
        ),
        testing_procedure=(
            "1. Obtain IT performance dashboards or scorecards and confirm they are issued regularly. "
            "2. Verify metrics are defined with targets (not just actuals). "
            "3. Check that performance reports are presented to the appropriate governance bodies. "
            "4. Review a sample of metrics: confirm underlying data sources are reliable. "
            "5. Confirm management actions are taken when metrics show performance below target."
        ),
        control_type=ControlType.DETECTIVE,
        automation_level=AutomationLevel.SEMI_AUTO,
        aliases=["performance monitoring", "IT metrics", "IT KPIs", "IT dashboard", "IT scorecard"],
    ))

    controls.append(Control(
        framework_id=framework_id,
        domain_id=mea.id,
        control_id_code="MEA02",
        title="Managed System of Internal Control",
        description=(
            "Continuously monitor and evaluate the control environment, including self-assessments "
            "and independent assurance reviews. Enable management and the board to have an "
            "effective and efficient internal control process for IT."
        ),
        objective=(
            "Obtain transparency for key stakeholders on the adequacy of the system of "
            "internal controls for IT and related assurance. Enable trust in IT operations "
            "and confidence in the IT internal control system."
        ),
        guidance=(
            "Establish a process for regularly assessing whether IT controls are designed "
            "well and working effectively. This means control self-assessments (CSAs) by "
            "management, plus independent reviews by internal audit. Maintain a control "
            "deficiency register and track remediation. In banking, the three lines of "
            "defence model requires IT management (1st line) to own its controls, a risk "
            "function (2nd line) to provide oversight, and internal audit (3rd line) to "
            "provide independent assurance."
        ),
        testing_procedure=(
            "1. Obtain evidence of control self-assessments performed by IT management. "
            "2. Review the IT control deficiency register — are deficiencies tracked and remediated? "
            "3. Confirm internal audit reviews IT controls and issues are tracked to closure. "
            "4. Verify control deficiencies are reported to the appropriate oversight bodies. "
            "5. Check that management provides a formal attestation on internal control effectiveness."
        ),
        control_type=ControlType.DETECTIVE,
        automation_level=AutomationLevel.MANUAL,
        aliases=["internal controls", "control self-assessment", "CSA", "IT audit oversight"],
    ))

    controls.append(Control(
        framework_id=framework_id,
        domain_id=mea.id,
        control_id_code="MEA03",
        title="Managed Compliance with External Requirements",
        description=(
            "Evaluate that IT and business processes are compliant with laws, regulations "
            "and contractual requirements. Obtain assurance that the requirements have been "
            "identified and complied with, and integrate IT compliance with overall "
            "enterprise compliance."
        ),
        objective=(
            "Ensure that the enterprise is compliant with all applicable external requirements. "
            "Provide certainty to senior management and the board that regulatory requirements "
            "are being met."
        ),
        guidance=(
            "Maintain a regulatory compliance register specifically for IT-related requirements. "
            "In banking this includes: OCC, FFIEC, GLBA, BSA/AML (for IT), payment system "
            "regulations, data privacy laws. Each requirement should have an owner and "
            "compliance evidence. Monitor regulatory developments — regulators frequently "
            "issue new guidance and updated examination procedures. Failure to track "
            "regulatory changes is itself a finding."
        ),
        testing_procedure=(
            "1. Obtain the IT regulatory compliance register — confirm all applicable regulations are listed. "
            "2. Verify each requirement has an owner and a compliance status. "
            "3. Review evidence supporting compliance with 3-5 key regulatory requirements. "
            "4. Confirm a process exists for monitoring regulatory developments and assessing their IT impact. "
            "5. Check that regulatory examination findings are tracked and remediated within required timeframes."
        ),
        control_type=ControlType.DETECTIVE,
        automation_level=AutomationLevel.MANUAL,
        aliases=["regulatory compliance", "IT compliance", "compliance management", "regulatory monitoring"],
    ))

    controls.append(Control(
        framework_id=framework_id,
        domain_id=mea.id,
        control_id_code="MEA04",
        title="Managed Assurance",
        description=(
            "Obtain assurance on whether IT services and controls are meeting the enterprise's "
            "requirements for the adequacy of the system of internal controls and the achievement "
            "of enterprise objectives. This includes assurance provided by internal and external "
            "parties."
        ),
        objective=(
            "Maintain appropriate levels of confidence in the achievement of enterprise objectives "
            "and the functioning of IT internal controls through independent assurance engagements. "
            "Support board and management oversight."
        ),
        guidance=(
            "This objective covers the assurance programme for IT — the combination of internal "
            "audit, external audit, SOC reports, penetration testing, and regulatory exams. "
            "Management should maintain an assurance map that shows what is covered, how "
            "frequently, by whom, and at what level of independence. Assurance findings should "
            "be tracked centrally. In banking, the combination of examiner findings, internal "
            "audit findings, and SOC report exceptions forms a comprehensive picture of the "
            "IT control environment."
        ),
        testing_procedure=(
            "1. Obtain the IT assurance plan or map — confirm it covers all significant IT risk areas. "
            "2. Verify internal audit completed its planned IT audit programme for the year. "
            "3. Review the consolidated assurance findings register — are all sources captured? "
            "4. Confirm findings are assigned owners, due dates, and tracked to closure. "
            "5. Check that the board or audit committee receives a consolidated assurance report."
        ),
        control_type=ControlType.DETECTIVE,
        automation_level=AutomationLevel.MANUAL,
        aliases=["IT assurance", "internal audit IT", "assurance mapping", "IT audit programme"],
    ))

    # ----------------------------------------------------------------
    # Insert all controls
    # ----------------------------------------------------------------

    for ctrl in controls:
        created = store.create_control(ctrl)
        print(f"  Created control: {created.control_id_code} — {created.title}")

    # ----------------------------------------------------------------
    # Summary
    # ----------------------------------------------------------------

    print(f"\nSeed complete.")
    print(f"  Framework : 1 (COBIT 2019)")
    print(f"  Domains   : 5 (EDM, APO, BAI, DSS, MEA)")
    print(f"  Controls  : {len(controls)} objectives")
    print(f"\nNext steps:")
    print(f"  1. Run: python -m seeds.verify_cobit to confirm data loaded correctly")
    print(f"  2. Then seed ISO 27001")
    print(f"  3. Then add cross-framework mappings")
    print(f"\nKNOWN ISSUE TO FIX: quality/input_gate.py regex currently requires")
    print(f"dot notation (BAI06.01). Update pattern to also match BAI06 format.")


if __name__ == "__main__":
    seed_cobit_2019()
