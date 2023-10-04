
[![Linter code check](https://github.com/coretex-ai/coretexpylib/actions/workflows/linter-code-check.yml/badge.svg?branch=develop)](https://github.com/coretex-ai/coretexpylib/actions/workflows/linter-code-check.yml)

![](https://coretex.ai/images/coretex_logo_new.svg)

<h1 style="text-align: center;">Coretex.ai Python library</h1>

Manage the complete lifecycle of your experiments and complex workloads, from project inception to production deployment and monitoring.

## What is Coretex.ai?

Coretex.ai is a powerful MLOps platform designed to make AI experimentation fast and efficient. With Coretex.ai, data scientists, ML engineers, and less experienced users can easily:

* Run their data processing experiments,
* Build AI models,
* Perform statistical data analysis,
* Run computational simulations.

Coretex.ai helps you iterate faster and with more confidence. You get reproducibility, scalability, transparency, and cost-effectiveness.

## Get started

**Step 1:** [Sign up for a free account ->](https://coretex.ai/)

**Step 2:** Install coretex:

```bash
$ pip install coretex
```

**Step 3:** Migrate your project to coretex:

```python
from coretex import CustomDataset, ExecutingExperiment


def main(experiment: ExecutingExperiment[CustomDataset]):
    # Remove "pass" and start task execution from here
    pass


if __name__ == "__main__":
    main()
```

Read the documentation and learn how you can migrate your project to the Coretex platform -> [Migrate your project to Coretex](https://app.gitbook.com/o/6QxmEiF5ygi67vFH3kV1/s/YoN0XCeop3vrJ0hyRKxx/getting-started/demo-experiments/migrate-your-project-to-coretex)

## Key Features

Coretex.ai offers a range of features to support users in their AI experimentation, including:

* **Task Templates:** Battle-tested templates that make training ML models and processing data simple,

* **Machine Learning Model Creation:** Quick and easy creation of machine learning models, with less friction and more stability,

* **Optimized Pipeline Execution:** Execution optimization of any computational pipeline, including large-scale statistical analysis and various simulations,

* **Team Collaboration:** The whole workflow in Coretex is centered around this concept to help centralize user management and enable transparent monitoring of storage and compute resources for administrators,

* **Dataset Management and Annotation Tools:** Powerful tools for managing and annotating datasets,

* **Run Orchestration and Result Analysis:** Detailed management of runs, ensuring reproducibility and easy comparison of results,

* **IT Infrastructure Setup:** Easy setup of IT infrastructure, whether connecting self-managed computers or using paid, dynamically scalable cloud computers,

* **Live Metrics Tracking:** Real-time tracking of run metrics during execution,

* **Artifact Upload and Management:** Easy upload and management of run artifacts, including models and results.

## Guaranteeing Reproducibility

One of the key benefits of Coretex.ai is its ability to guarantee reproducibility. The platform keeps track of all configurations and parameters between runs, ensuring that users never lose track of their work.

## Supported Use Cases

Coretex.ai is a versatile platform that can be used for a variety of use cases, including:

* Training ML models,
* Large-scale statistical analysis,
* Simulations (physics, molecular dynamics, population dynamics, econometrics, and more).

## Compatibility with other libraries

Coretex is compatible with all ML libraries such as Wandb, Tensorboard, PyTorch, and etc. There are no limits when it comes to Coretex integration with other libraries.

## Support

If you require any assistance or have any questions, our support team is available to help. Please feel free to reach out to us through our contact page or via email support@coretex.ai. We will be happy to assist you with any inquiries or issues you may have. Check out the Coretex platform overview at [coretex.ai](https://www.coretex.ai) for more information, tutorials, and documentation.
