# Prompting Guide

## Metaprompting

Metaprompting is prompting about prompting.

Instead of asking a model to directly do the task, you first improve the process used to solve it.

That can mean asking the model to:

- design a better prompt
- choose a reasoning structure
- break the task into steps
- define quality criteria
- simulate an expert role
- refine its own instructions before answering

The target is not only the final output. The target is also the process specification that produces a better output.

---

## Simple Distinction

Normal prompting:

> Write a Python script that parses a CSV and inserts rows into PostgreSQL.

Metaprompting:

> Before answering, create the best possible prompt for a senior Python engineer to build a robust CSV-to-PostgreSQL importer with validation, retries, logging, and type hints. Then use that prompt to produce the solution.

The second version adds a layer of abstraction:

1. define how the model should think
2. then do the work

---

## Why It Matters

Metaprompting is useful when the task is:

- vague
- complex
- high-stakes
- multi-step
- easy to answer badly with a shallow response

It helps because it forces:

- better structure
- clearer assumptions
- explicit constraints
- output formatting
- evaluation criteria

Without that, prompts are often underspecified and the model fills gaps arbitrarily.

---

## What It Is Not

Metaprompting is not magic.
It does not automatically make the model smarter.

It mainly improves:

- task framing
- consistency
- completeness
- relevance

If the request itself is nonsense, metaprompting just produces better-structured nonsense.

---

## Main Forms Of Metaprompting

### 1. Prompt Generation

Ask the model to write the best prompt for a task.

Example:

> Generate an optimal prompt to analyze a network outage RCA for technical accuracy, root cause clarity, and executive readability.

Use this when you want a reusable prompt.

### 2. Role And Standard Definition

Define expertise, criteria, and workflow before execution.

Example:

> Act as a principal NetDevOps engineer. First define the evaluation rubric for a production-safe BGP automation script, then review the code against that rubric.

This is stronger than `review this code` because the rubric creates a stable evaluation basis.

### 3. Decomposition

Break a large task into subproblems before solving it.

Example:

> Break this migration into discovery, dependency mapping, rollback planning, implementation, and validation. Then work through each phase.

### 4. Self-Critique And Refinement

Produce a draft, critique it, then improve it.

Example:

> Draft the proposal. Then identify weaknesses in clarity, persuasion, and technical completeness. Then produce a revised version.

### 5. Output Schema Design

Define the answer structure before filling it in.

Example:

> Define the best output format for comparing Python TUI frameworks for enterprise use. Then fill it in.

---

## How To Use It Well

### 1. Start With The Real Objective

Weak:

> Explain BGP.

Better:

> Explain BGP to a network engineer transitioning into automation, focusing on operational concepts needed for troubleshooting ISP edge routers.

### 2. Ask For Assumptions Explicitly

A common failure mode is hidden assumptions.

Example:

> Before solving, list the assumptions you are making about environment, scale, constraints, and audience.

This matters a lot in:

- architecture
- debugging
- planning
- business writing
- automation design

### 3. Force Criteria

Tell the model what good means.

Example:

> Optimize for correctness, operational safety, and maintainability. Avoid clever but fragile solutions.

Without criteria, the model may optimize for fluency instead of usefulness.

### 4. Separate Planning From Execution

A strong metaprompt usually has two stages:

1. define the approach
2. execute the approach

Example:

> First define the best strategy to answer this. Then apply it.

### 5. Use Constraints Aggressively

Constraints improve quality.

Examples:

- Do not use tables.
- Assume Python 3.12.
- Target Ubuntu 24.04.
- Give only production-safe commands.
- Avoid vendor-locked solutions.
- Cite official docs.

---

## Practical Templates

### Template 1: General Expert Work

You are an expert in `[domain]`.

Before answering:
1. Restate the task precisely.
2. List assumptions you must make.
3. Define the criteria for a high-quality answer.
4. Choose the best response structure.

Then produce the final answer.

Optimize for: `[accuracy / depth / brevity / safety / practicality]`
Avoid: `[common failure modes]`
Audience: `[target audience]`

### Template 2: Better Technical Answers

Act as a senior engineer.

First define the best approach, including:

- assumptions
- dependencies
- tradeoffs
- failure modes
- validation steps

Then solve the problem using that approach.

Context:

`[paste context]`

Constraints:

`[paste constraints]`

Output:

- explanation
- implementation
- tests
- risks

### Template 3: Prompt Generator

Create the best possible prompt for an AI assistant to complete this task.

Task:

`[paste task]`

The prompt should:

- specify the role
- include necessary context
- define constraints
- require assumptions to be stated
- specify output format
- include a quality checklist

After generating the prompt, use it to complete the task.

### Template 4: Self-Critique Loop

Complete the task in three phases:

1. produce a first draft
2. critique it for missing assumptions, weak reasoning, and poor structure
3. produce an improved final version

### Template 5: Decision-Making

Help me decide between `[option A]` and `[option B]`.

Before recommending anything:

1. define the decision criteria
2. identify what information is missing
3. state reasonable assumptions where needed
4. compare the options against the criteria
5. give a recommendation and explain when it would fail

---

## Good Use Cases

Metaprompting works especially well for:

- architecture decisions
- code generation
- code review
- debugging
- study plans
- proposal writing
- document summarization with structure
- interview prep
- business analysis
- research synthesis

It is less necessary for:

- simple factual definitions
- short translations
- trivial formatting requests

Using metaprompting for everything with the same heavy process is inefficient. The process should scale with task complexity.

---

## Weak Vs Strong

Weak:

> Compare Textual and Ink.

Better:

> Compare Textual and Ink for building an interactive terminal UI that supports mouse input, dynamic state updates, async background tasks, and long-term maintainability.
>
> Before answering, define the decision criteria most relevant to this use case. Then compare both frameworks against those criteria. End with a recommendation, key tradeoffs, and failure cases.

---

## Project-Specific Usage For netbox-sdk

This project should use metaprompting as an internal workflow, especially for:

- TUI design and theme work
- Textual widget composition
- CLI/TUI parity decisions
- NetBox API design and schema-driven behavior
- production-safety review
- debugging and regression fixing
- documentation changes that affect contributor workflow

For `netbox-sdk`, a strong internal prompt usually includes:

- role: senior Python engineer, principal NetDevOps architect, or Textual UI specialist
- context: NetBox API-first CLI/TUI project
- objective: exact user or contributor outcome
- constraints: async-first, schema-driven, theme-safe, testable, production-safe
- evaluation criteria: correctness, maintainability, safety, UX consistency
- output shape: plan, implementation, tests, risks
- refinement step: self-critique or verification pass

Example for architecture:

> Act as a principal NetDevOps architect.
>
> I want to design a network automation service for ISP operations.
>
> Before proposing anything:
> 1. identify the operational goals
> 2. list assumptions about scale, reliability, vendors, and source of truth
> 3. define architecture evaluation criteria
> 4. identify common failure modes
>
> Then propose:
> - architecture
> - data model
> - job execution model
> - rollback strategy
> - observability
> - security controls
> - testing strategy
>
> Optimize for operational safety, maintainability, and incremental adoption. Avoid hand-wavy abstractions.

Example for code review:

> Review this Python code as if it were going into production at an ISP.
>
> Before reviewing, define the rubric across:
> - correctness
> - concurrency safety
> - error handling
> - observability
> - maintainability
> - API design
> - typing
> - testability
>
> Then review the code against the rubric and propose specific fixes in priority order.

---

## Common Mistakes

### 1. Too Meta, No Task

Bad:

> Write the best prompt for my project.

That is empty. Best for what?

### 2. Overloaded Metaprompts

Huge prompts with too many rules often degrade quality because the instructions conflict.

Clarity matters more than prompt bloat.

### 3. No Output Constraints

Without an output form, the model may produce a polished but unusable essay.

### 4. Fake Rigor

Weak instructions:

- think deeply
- use maximum intelligence
- reason like a genius

Useful instructions:

- define assumptions
- compare tradeoffs
- show edge cases
- produce tests

### 5. Treating Self-Critique As Truth

Self-critique can still be wrong.
Metaprompting improves process, not guarantees correctness.

Validation is still required.

---

## Compact Formula

A strong metaprompt usually contains:

`Role + Context + Objective + Constraints + Evaluation Criteria + Output Format + Refinement Step`

Example:

> Act as a senior Python engineer.
>
> Context:
> I am building a CLI/TUI NetBox client for production use.
>
> Objective:
> Design the best architecture for reliability and maintainability.
>
> Constraints:
> - Python 3.12
> - async-first
> - schema-driven
> - must support testing and future TUI integration
>
> Evaluation criteria:
> - correctness
> - extensibility
> - simplicity
> - operational safety
>
> Output:
> - architecture decision
> - alternatives considered
> - tradeoffs
> - recommended implementation plan
> - risks
> - example code skeleton
>
> Then critique your own recommendation and revise it.

---

## Bottom Line

Metaprompting is not a prompt trick.
It is explicit process design for prompting.

Use it when:

- the task is underspecified
- quality matters
- you want the model to expose or improve its framework before producing the answer

The practical benefit is not magic intelligence.
It is reduced ambiguity and better structured output.

For this project, the goal is simple:

- better prompting should produce better code changes
- better prompt structure should produce better reviews
- better internal framing should reduce shallow or arbitrary implementation decisions
