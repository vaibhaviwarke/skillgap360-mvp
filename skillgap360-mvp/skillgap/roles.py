"""Target-role skill templates and the proficiency scale used by the Skill Passport.

The AI only rates the skills listed for the chosen role, so the output is always
comparable and the gap calculation stays deterministic (no second AI call).
"""

# Proficiency scale shared by the AI prompt, the review table and the passport.
LEVELS = {
    0: "No evidence",
    1: "Basic – learned or certified, no real project use",
    2: "Working – used in at least one real project",
    3: "Strong – used repeatedly or independently across projects",
    4: "Expert – leads, designs or teaches others",
}

LEVEL_SHORT = {0: "0 · None", 1: "1 · Basic", 2: "2 · Working", 3: "3 · Strong", 4: "4 · Expert"}

# Weight = how much the skill matters for the role (3 critical, 2 important, 1 nice to have).
WEIGHT_LABEL = {3: "Critical", 2: "Important", 1: "Nice to have"}

ROLE_TEMPLATES = {
    "ML Engineer": {
        "description": "Builds, trains and deploys machine-learning models into production systems.",
        "skills": [
            {"name": "Python programming", "target": 3, "weight": 3,
             "next_step": "Rebuild one of your existing scripts as a clean Python package with tests. Resource: Kaggle Learn – Python and Pandas."},
            {"name": "Statistics and probability", "target": 2, "weight": 3,
             "next_step": "Work through hypothesis testing and regression, then explain one model's errors to a peer. Resource: Khan Academy – Statistics and Probability."},
            {"name": "Machine learning algorithms", "target": 3, "weight": 3,
             "next_step": "Train and compare three models on a work-like dataset and write up the trade-offs. Resource: Google Machine Learning Crash Course."},
            {"name": "Data wrangling (SQL, pandas)", "target": 3, "weight": 2,
             "next_step": "Turn a messy CSV or database extract into a model-ready dataset with documented cleaning steps. Resource: Kaggle Learn – Data Cleaning."},
            {"name": "Deep learning frameworks (PyTorch, TensorFlow)", "target": 2, "weight": 2,
             "next_step": "Fine-tune a small pretrained model on a text or image task. Resource: official PyTorch tutorials."},
            {"name": "MLOps and model deployment", "target": 2, "weight": 2,
             "next_step": "Wrap a trained model in an API, containerise it and add a CI check. Resource: Made With ML (MLOps course)."},
            {"name": "Software engineering practices (Git, testing, code review)", "target": 3, "weight": 2,
             "next_step": "Add unit tests and a code-review checklist to an ML notebook project."},
            {"name": "Cloud ML platform (Azure ML, SageMaker, Vertex AI)", "target": 2, "weight": 1,
             "next_step": "Deploy one model to a managed endpoint on your company's cloud. Resource: Microsoft Learn – Azure Machine Learning paths."},
        ],
    },
    "Cloud Engineer (Azure)": {
        "description": "Designs, automates and runs cloud infrastructure for client applications.",
        "skills": [
            {"name": "Azure core services", "target": 3, "weight": 3,
             "next_step": "Deploy a small web app with storage, networking and identity on Azure. Resource: Microsoft Learn – AZ-104 path."},
            {"name": "Infrastructure as code (Terraform, Bicep)", "target": 3, "weight": 3,
             "next_step": "Recreate that deployment in Terraform and destroy and rebuild it from code. Resource: HashiCorp Developer tutorials."},
            {"name": "Containers and orchestration (Docker, Kubernetes)", "target": 2, "weight": 3,
             "next_step": "Containerise one service and run it on a managed Kubernetes cluster. Resource: kubernetes.io basics tutorial."},
            {"name": "CI/CD pipelines", "target": 3, "weight": 2,
             "next_step": "Build a pipeline that tests, builds and deploys on every merge. Resource: Microsoft Learn – Azure Pipelines."},
            {"name": "Linux and networking", "target": 2, "weight": 2,
             "next_step": "Troubleshoot DNS, ports and firewall rules on a Linux VM you set up yourself."},
            {"name": "Scripting (Python, PowerShell, Bash)", "target": 2, "weight": 2,
             "next_step": "Automate one repetitive operations task end to end with a script."},
            {"name": "Cloud security and IAM", "target": 2, "weight": 2,
             "next_step": "Apply least-privilege roles and secrets management to your demo deployment. Resource: Microsoft Learn – AZ-500 modules."},
            {"name": "Monitoring and observability", "target": 2, "weight": 1,
             "next_step": "Add dashboards and alerts for one service using Azure Monitor."},
        ],
    },
    "Data Engineer": {
        "description": "Builds reliable data pipelines and platforms that analytics and AI teams depend on.",
        "skills": [
            {"name": "SQL", "target": 3, "weight": 3,
             "next_step": "Write window-function and performance-tuned queries on a large dataset. Resource: SQLBolt, then your company warehouse."},
            {"name": "ETL/ELT pipeline development", "target": 3, "weight": 3,
             "next_step": "Build an incremental pipeline from a source system to a warehouse with error handling."},
            {"name": "Python for data engineering", "target": 2, "weight": 3,
             "next_step": "Replace one manual data task with a tested Python job."},
            {"name": "Data modelling and warehousing", "target": 2, "weight": 2,
             "next_step": "Design a star schema for one business process and document it."},
            {"name": "Big data processing (Spark)", "target": 2, "weight": 2,
             "next_step": "Process a multi-GB dataset with Spark and compare against pandas. Resource: Apache Spark quick start."},
            {"name": "Cloud data services (Data Factory, Databricks, Snowflake)", "target": 2, "weight": 2,
             "next_step": "Rebuild your pipeline on a managed cloud data service. Resource: Microsoft Learn – DP-900 then DP-203 paths."},
            {"name": "Workflow orchestration (Airflow)", "target": 2, "weight": 1,
             "next_step": "Schedule your pipeline as a DAG with retries and alerts. Resource: Apache Airflow tutorial."},
            {"name": "Data quality and governance", "target": 2, "weight": 1,
             "next_step": "Add automated data-quality checks and lineage notes to one pipeline."},
        ],
    },
}


def role_names():
    return list(ROLE_TEMPLATES.keys())


def role_skills(role_name):
    return ROLE_TEMPLATES[role_name]["skills"]
