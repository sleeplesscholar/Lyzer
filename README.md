# lyZer --- AI-Assisted Circuit Inspection

lyZer is a web application concept that aims to help people inspect
electrical and electronic circuits using AI. Users upload a photograph
of a circuit, and the system analyzes the visible components and
connections to provide useful feedback about possible issues and safety
considerations.

The goal is to make circuit inspection more approachable for learners
and hobbyists while also supporting practical troubleshooting.

## The idea

The planned workflow has three main steps:

1.  **Upload a circuit photo** --- The user takes or selects a
    photograph and uploads it to the web app.
2.  **Analyze with AI** --- An AI model examines visible components and
    connections, then helps identify possible failure points or
    concerns.
3.  **Get actionable feedback** --- The app explains what it can infer,
    highlights uncertainty, and offers relevant troubleshooting
    suggestions and safety guidance.

### Intended capabilities

-   Recognize visible circuit components where the image and model make
    that possible.
-   Describe visible connections and potential issues for the user to
    investigate.
-   Offer explanatory feedback that helps users learn as they
    troubleshoot.
-   Provide cautious, general safety guidance and recommend verification
    steps.
-   Make the interface approachable for both learning and practical
    analysis.

These are project goals, not a claim that every capability is already
implemented. Model accuracy will need to be tested against real circuit
photographs and known examples.

## Planned AI technology: Gemma 4

lyZer is intended to explore **Gemma 4**, Google's family of open-weight
AI models. Gemma 4 includes models designed for multimodal tasks,
including vision, which makes it a candidate for experimenting with
circuit-photo analysis.

A possible processing flow is:

1.  The web interface accepts a circuit photograph.
2.  The application sends the image and a carefully designed prompt to
    the selected Gemma 4 model.
3.  The model returns a structured description of visible components,
    possible concerns, uncertainty, and suggested checks.
4.  The interface presents the response in readable language.

Official references: - [Gemma 4 model
overview](https://ai.google.dev/gemma/docs/core) - [Gemma 4
license](https://ai.google.dev/gemma/docs/gemma_4_license)

## Open-source licensing

lyZer intends to use open-source licensing so others can inspect, learn
from, modify, and build on the project's own code.

### lyZer code --- MIT License

The project's original source code may be released under the **MIT
License**. It is a permissive license that generally allows people to
use, copy, modify, merge, publish, distribute, sublicense, and sell
copies of the licensed software, provided the copyright and license
notice are included.

The MIT License also states that the software is provided "as is",
without warranty. This is particularly relevant to lyZer: the project
should not promise that its output is error-free or that following an
AI-generated suggestion guarantees electrical safety.

To apply the MIT License, the repository should include a `LICENSE` file
containing the full MIT License text and the correct copyright holder
and year. For example, the copyright line can be completed as:

`Copyright (c) 2026 Lyzer Team`

Use the actual rights holder and year that fit the project; do not claim
ownership of third-party code.

Reference: [MIT License --- Open Source
Initiative](https://opensource.org/license/mit)

### AI model --- Gemma 4 license

Gemma 4 is **not covered by lyZer's MIT License**. Google's official
Gemma 4 release information states that Gemma 4 is released under the
**Apache License 2.0**. The model and its weights therefore have their
own license terms, separate from the license used for lyZer's original
code.

In practice:

-   The MIT License applies to the lyZer code that the project authors
    choose to license under MIT.
-   The Apache 2.0 license applies to Gemma 4 components covered by that
    license.
-   Other libraries, frameworks, model files, and assets may have their
    own licenses and notices.
-   If Gemma 4 model files are redistributed with the project, retain
    the required license and notice information and follow the
    applicable Apache 2.0 terms.
-   Before publishing a release, check the exact model variant and the
    license files for every dependency and asset included.

References: - [Google's Gemma 4
announcement](https://opensource.googleblog.com/2026/03/gemma-4-expanding-the-gemmaverse-with-apache-20.html) -
[Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0)

## Safety and responsible feedback

Because lyZer is intended to discuss electrical circuits, safety needs
to be considered from the beginning.

-   Clearly distinguish visible observations from guesses or uncertain
    inferences.
-   Avoid claiming that a circuit is safe based only on a photograph.
-   Explain that hidden connections, component ratings, power sources,
    and real operating conditions may not be visible.
-   Encourage users to verify suggestions with measurements, datasheets,
    established procedures, and qualified help.
-   Do not encourage users to handle energized or hazardous circuits
    without appropriate training and precautions.
-   Test the system with a range of circuit types, image quality levels,
    and deliberately ambiguous examples.

AI output should support human understanding and verification rather
than replace them.

## Current scope and future work

The immediate goal is to build and evaluate the core photo-to-feedback
experience. The following items may be developed or improved over time:

-   Circuit image upload and validation.
-   Prompting and response formatting for the selected Gemma 4 model.
-   Component identification and potential-issue reporting.
-   Clear explanations, confidence/uncertainty indicators, and safety
    guidance.
-   Testing against labeled example circuits.
-   A persistent discussion forum or saved analysis history, if needed
    later.

A basic forum prototype may currently use client-side JavaScript and
sample discussions only. Without a backend or database, user-submitted
comments are not permanently stored and will disappear when the page is
refreshed.

## Project status

**Status:** Concept / active development.

The features described here are intended goals. Implementation details
and model performance may change as the project is built and tested.

## Contributing

Contributions, feedback, bug reports, and ideas are welcome. Before
contributing, check the licenses of any third-party code, model files,
datasets, or assets you add. Do not include material unless you have
permission to use and redistribute it under the intended terms.

## License summary

  -----------------------------------------------------------------------
  Project component                   Intended license / terms
  ----------------------------------- -----------------------------------
  Original lyZer code                 MIT License, once the repository
                                      includes its `LICENSE` file

  Gemma 4 model                       Apache License 2.0, subject to the
                                      exact official model release

  Third-party dependencies and assets Their own respective licenses
  -----------------------------------------------------------------------

This summary is for project documentation and is not a substitute for
reviewing the full licenses.
