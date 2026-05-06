---
name: foundation-concepts
description: Document programming language concepts using Robert W. Sebesta's theory and vocabulary. Apply when creating educational material about language features, abstractions, or control flow.
user-invocable: true
argument-hint: [concept-name]
---

# Sebesta Concepts Documentation

## When to Use

Use this skill when documenting concepts that should be grounded in established theoretical frameworks. Apply when:

- Explaining a language feature (yield, async, coroutines, etc.)
- Categorizing a design pattern or architectural pattern
- Analyzing algorithmic problems or solutions
- Comparing implementations across languages or systems

## Reference Frameworks

Classify concepts using these established taxonomies and cite authoritative sources:

### Sebesta (Programming Language Theory)

**Source:** Robert W. Sebesta — _Concepts of Programming Languages_ (12th ed., 2019)

**Control Flow:** Sequential, conditional, iterative, subprogram invocation, exception handling
**Abstraction:** Data abstraction, procedural abstraction, iterator abstraction, coroutines
**Evaluation:** Eager, lazy, short-circuit
**Types:** Explicit, implicit, gradual
**Concurrency:** Sequential, parallel, concurrent, asynchronous

### GoF Design Patterns

**Source:** Gang of Four — Erich Gamma, Richard Helm, Ralph Johnson, John Vlissides
— _Design Patterns: Elements of Reusable Object-Oriented Software_ (1994)

**Creational:** Singleton, Factory, Abstract Factory, Builder, Prototype
**Structural:** Adapter, Bridge, Composite, Decorator, Facade, Flyweight, Proxy
**Behavioral:** Chain of Responsibility, Command, Iterator, Mediator, Memento, Observer, State, Strategy, Template Method, Visitor, Interpreter

### EIP (Enterprise Integration Patterns)

**Source:** Gregor Hohpe & Bobby Woolf — _Enterprise Integration Patterns: Designing, Building, and Deploying Messaging Solutions_ (2003)

**Messaging:** Publish-Subscribe, Point-to-Point, Request-Reply, One-Way
**Routing:** Content-Based Router, Dynamic Router, Recipient List, Splitter, Aggregator
**Transformation:** Message Translator, Envelope Wrapper, Content Enricher, Claim Check
**Management:** Dead Letter Channel, Resequencer, Idempotent Consumer, Transaction Log

### Enterprise Design Patterns

**Source:** Sam Newman — _Building Microservices_ (2nd ed., 2021)
**Alternative:** Chris Richardson — _Microservices Patterns_ (2018)

**Architectural:** Service Mesh, API Gateway, CQRS, Event Sourcing, Saga Pattern
**Resilience:** Circuit Breaker, Retry, Timeout, Bulkhead, Rate Limiting
**Data:** Database per Service, Event Store, Eventual Consistency
**Decomposition:** By Business Capability, By Subdomain (Domain-Driven Design)

### Algorithm Analysis

**Source:** Cormen, Leiserson, Rivest, Stein — _Introduction to Algorithms_ (CLRS, 3rd ed., 2009)
**Alternative:** Robert Sedgewick & Kevin Wayne — _Algorithms_ (4th ed., 2011)

**Problem Classes:** Sorting, searching, graph traversal, dynamic programming, greedy, divide-and-conquer
**Complexity:** Big O/Θ/Ω, time, space, best/average/worst case
**Data Structures:** Arrays, linked lists, stacks, queues, trees, heaps, hash tables, graphs
**Paradigms:** Iteration, recursion, memoization, bottom-up, top-down

### Network Fundamentals

**Source:** James F. Kurose & Keith W. Ross — _Computer Networking_ (8th ed., 2020)

**OSI Model:** Application, Transport, Internet, Link, Physical layers
**Protocols:** HTTP/HTTPS, TCP/UDP, IP, DNS, SMTP, FTP
**Concepts:** Packet switching, routing, congestion control, flow control, reliability
**Architectures:** Client-server, peer-to-peer, hybrid

### Additional Foundational References

**Domain-Driven Design:** Eric Evans — _Domain-Driven Design: Tackling Complexity in the Heart of Software_ (2003)

**Software Architecture:** Mark Richards & Neal Ford — _Fundamentals of Software Architecture_ (2020)

**Concurrency:** Maurice Herlihy & Nir Shavit — _The Art of Multiprocessor Programming_ (3rd ed., 2020)

## Documentation Structure

When creating concept documentation, follow this template:

```markdown
# [Concept Name]

## Sebesta Classification

- **Category**: [Control Flow / Abstraction / Evaluation / Type / Concurrency]
- **Type**: [specific subcategory]
- **Implementations**: [languages that implement it]

## Definition

[1-2 sentences defining the concept theoretically, grounded in Sebesta]

## Mechanism

[How it works at the language level]

## Python

[Specific feature/syntax in Python]

### Idiomatic Python

[How experienced Python developers use this idiomatically. Common patterns, best practices, PEP 8 / community guidelines. Real code patterns from popular libraries like requests, Django, asyncio. What senior Pythonistas expect to see.]

### References

**Books**: [e.g., Fluent Python by Luciano Ramalho, Chapter X]
**Authorities**: [e.g., Raymond Hettinger, David Beazley]
**Code**: [e.g., cpython implementation, Django ORM source, requests library]
**Standards**: [e.g., PEP 20, PEP 8, relevant PEP number]

## Go

[Specific feature/syntax in Go]

### Idiomatic Go

[How Go developers idiomatically use this. Go philosophy (simplicity, readability, explicit error handling). Conventions from golang/wiki. Patterns from standard library and popular projects. What experienced Go developers prefer.]

### References

**Books**: [e.g., The Go Programming Language by Donovan & Kernighan]
**Authorities**: [e.g., Rob Pike, Dave Cheney]
**Code**: [e.g., golang/go stdlib, Kubernetes, Docker]
**Standards**: [e.g., Effective Go, Go Code Review Comments]

## Ruby

[Specific feature/syntax in Ruby]

### Idiomatic Ruby

[How Ruby developers use this idiomatically. Ruby philosophy (developer happiness, metaprogramming conventions). Patterns from Rails and Ruby community. What Rubyists idiomatically prefer — blocks, duck typing, conventions over configuration.]

### References

**Books**: [e.g., Programming Ruby (The Pickaxe), Eloquent Ruby by Russ Olsen]
**Authorities**: [e.g., Matz, Sarah Mei]
**Code**: [e.g., ruby/ruby, Rails source, RSpec]
**Standards**: [e.g., Ruby Style Guide, RUPs]

## JavaScript

[Specific feature/syntax in JavaScript]

### Idiomatic JavaScript

[How JavaScript developers use this idiomatically. ES6+ conventions. Community patterns (Node.js, browser, frameworks). What senior JavaScript developers expect to see. Async patterns, functional paradigms, common libraries.]

### References

**Books**: [e.g., You Don't Know JS by Kyle Simpson, JavaScript: The Definitive Guide]
**Authorities**: [e.g., Kyle Simpson, Brendan Eich]
**Code**: [e.g., v8/v8, Node.js, React, lodash]
**Standards**: [e.g., ECMAScript spec, MDN Web Docs, TC39 proposals]

## Other Languages

[Brief coverage of other implementations (Java, Rust, Lisp, Elixir, etc.) — mention language, mechanism, and key idiom if relevant]

### References (if applicable)

**Books**: [Language-specific authoritative books]
**Authorities**: [Language creators or experts]
**Code**: [Canonical repositories or popular libraries]
**Standards**: [Official language docs or RFCs]

## Related Concepts

[List related concepts, how they differ]

## Examples

[Concrete code examples — include idiomatic patterns alongside basic usage. Source each example where possible (e.g., "From Django ORM source", "As used in Kubernetes", "Common pattern in Node.js")]
```

## Vocabulary Rules

1. **Use Sebesta's terms precisely**
   - "Generator" = Sebesta concept (produces sequence under demand)
   - "yield" = Python mechanism implementing generators
   - Not: "yield is a generator" → Correct: "yield implements generators"

2. **Distinguish concept from implementation**
   - Concept: "Coroutine — subprogram with multiple entry/exit points"
   - Python implementation: "async def + await"
   - Go implementation: "goroutines + channels"

3. **Classify by Sebesta category first**
   - Example: "Yield is a control flow mechanism that implements the generator abstraction"
   - Not: "Yield pauses a function"

4. **Compare across languages using theory**
   - All use the same Sebesta concept (generator, coroutine, iterator)
   - Different mechanisms (yield vs channels vs function\*)

5. **Avoid mixing levels**
   - Don't explain Python syntax as if it's universal theory
   - Do ground Python in Sebesta theory

6. **Always include idiomatic usage**
   - Theory: mechanism and how it works
   - Idiom: how practitioners use it in real code (style, conventions, best practices)
   - Real-world: what senior developers expect to see, common patterns from popular libraries
   - Example: generators are used idiomatically with `for` loops or `next()`, not by manually calling `__next__()`

## Anti-patterns

❌ "Generator is when you use yield"
✅ "Generator is a Sebesta concept (producing sequences under demand). Python implements it via yield. Idiomatically, Python developers use `for x in generator:` rather than calling `__next__()` directly."

❌ "Async/await is async programming"
✅ "Async/await is a mechanism for implementing coroutines in a single-threaded event loop. In JavaScript, developers idiomatically use `await` inside `async` functions; in Python, they use `await` with libraries like `asyncio`."

❌ "Recursion is when a function calls itself"
✅ "Recursion is a control flow mechanism where a subprogram invokes itself, transferring control to a new activation record. Idiomatically, Lispers embrace recursion heavily, while Python developers prefer iteration for performance reasons."

❌ Ignoring language-specific conventions
✅ "This concept works the same way theoretically, but experienced developers in each language use it differently — document those idioms explicitly (Go: channels for concurrency; Python: generators + iterators; JavaScript: async/await)."

## Language-Specific References

When documenting idioms and practices, cite authoritative sources:

### Python

- **Books**: Fluent Python (Luciano Ramalho), Effective Python (Brett Slatkin), Python Cookbook (David Beazley & Brian K. Jones)
- **Authorities**: Guido van Rossum (creator), Raymond Hettinger, David Beazley, Armin Ronacher
- **Repositories**: cpython, requests, Django, asyncio (stdlib), attrs
- **Standards**: PEP 8 (Style Guide), PEP 20 (Zen of Python), relevant enhancement proposals

### Go

- **Books**: The Go Programming Language (Donovan & Kernighan), Go Concurrency Patterns (talks)
- **Authorities**: Rob Pike, Robert Griesemer, Ken Thompson, Dave Cheney
- **Repositories**: golang/go, standard library, popular projects (Kubernetes, Docker)
- **Standards**: golang/wiki, Effective Go, Go Code Review Comments

### Ruby

- **Books**: Programming Ruby (The Pickaxe), Eloquent Ruby (Russ Olsen), The Ruby Way (Hal Fulton)
- **Authorities**: Matz (Yukihiro Matsumoto), Why the Lucky Stiff, Sarah Mei
- **Repositories**: ruby/ruby, Rails, Sinatra, RSpec
- **Standards**: Style Guide, Ruby Enhancement Proposals (RUPs)

### JavaScript

- **Books**: You Don't Know JS (Kyle Simpson), JavaScript: The Definitive Guide (David Flanagan), Eloquent JavaScript (Marijn Haverbeke)
- **Authorities**: Kyle Simpson, Brendan Eich, Mark Dalgleish, Wesbos (Wes Bos)
- **Repositories**: v8/v8, Node.js, React, TypeScript, lodash, express
- **Standards**: ECMAScript spec, MDN Web Docs, TC39 proposals

## Output Location

Documentation should go to: `/Users/${USER}/studies/concepts/`

Name files by concept: `generator.md`, `coroutine.md`, `yield.md`, etc.

## Template File

See `template.md` for a pre-filled example.
