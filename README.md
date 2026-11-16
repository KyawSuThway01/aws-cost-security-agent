# aws-cost-security-agent

An AI agent that reviews one AWS account for cost waste and security problems,
explains each problem in simple words, and ranks it by risk.

**The agent is read-only. It cannot change anything.** Any fix needs a human
to approve it, and the fix runs through a separate tool with its own limited role.

## What it does

- Finds public S3 buckets, security groups open to the whole internet, and idle EC2 servers.
- Reads month-to-date spend from Cost Explorer.
- Produces a structured JSON report, sorted by risk in code (not left to the model).
- Includes a separate fixer that can turn on S3 Block Public Access, only after
  a dry run, a typed confirmation, and an MFA code.

## Architecture

```mermaid
flowchart LR
    subgraph ReadOnly["Read-only side"]
        Agent["Agent (Strands + Claude)"] --> Tools["Read-only tools + secret redaction"]
        Tools --> ScanRole["IAM user: agent-readonly"]
        ScanRole --> AWS["AWS account"]
    end
    Agent --> Report["JSON report"]
    Human(["Human"]) --> Report
    Human --> Fixer["Fixer CLI"]
    subgraph Approval["Fix side (human in the loop)"]
        Fixer --> Recheck["Live re-check"]
        Recheck --> DryRun["Dry run by default"]
        DryRun --> Confirm["Human types bucket name"]
        Confirm --> MFA["MFA code"]
        MFA --> FixRole["IAM role: agent-fixer-s3"]
        FixRole --> AWS
    end
    Fixer --> Audit["Audit log"]
```