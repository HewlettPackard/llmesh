# HPE Contribution Guide

Hi there! We're thrilled that you'd like to contribute to this project. Your help is essential for keeping it great.

Please note that this project is released with a [Contributor Code of Conduct](CODE-OF-CONDUCT.md). By participating in this project you agree to abide by its terms.

This guide provides information on filing issues and guidelines for open source contributors. **Please leave comments / suggestions if you find something is missing or incorrect.**

Contributors are encouraged to collaborate using the Slack channels in addition to the GitHub.

If you have questions, feedback or concerns please let us know (<github@hpe.com>).

## Contributing

You are invited to contribute new features, fixes, or updates, large or small; we are always thrilled to receive pull requests, and do our best to process them as fast as we can.

Before you start to code, we recommend discussing your plans with the targeted project/repo through a GitHub issue, especially for more ambitious contributions. This gives other contributors a chance to point you in the right direction, give you feedback on your design, and help you find out if someone else is working on the same thing.

* If you want to contribute design assets or style guide revisions, please open a GitHub pull request or open a GitHub issue against the particular project.
* If you want to raise an issue such as a defect or an enhancement request, please open a GitHub issue for the appropriate project. Please keep the following in mind:

  * Try to reduce your code to the bare minimum required to reproduce the issue.
  * If we can't reproduce the issue, we can't fix it. Please list the exact steps required to reproduce the issue.

## Issues

PLEASE READ: If the issue is a security vulnerability, please follow the guidelines in our [security section](SECURITY.md).

If you have suggestions for how this project could be improved, or want to report a bug, open an issue! We'd love all and any contributions. If you have questions, too, we'd love to hear them.

It is a great way to contribute to [Athon/LAT-Mesh] by reporting an issue. Well-written and complete bug reports are always welcome! Please open an issue on GitHub and follow the template to fill in required information.

Before opening any issue, please look up the existing [issues] to avoid submitting a duplication.
If you find a match, you can "subscribe" to it to get notified on updates. If you have additional helpful information about the issue, please leave a comment.

When reporting issues include details but, because the issues are open to the public, when submitting the log and configuration files, be sure to remove any sensitive information, e.g. user name, password, IP address, and company name. You can replace those parts with "REDACTED" or other strings like "****".

Be sure to include the steps to reproduce the problem if applicable. It can help us understand and fix your issue faster.

## Testing

As this open-source project serves as a wrapper around low-level libraries, it is crucial to focus on integration testing and end-to-end (E2E) testing. Contributors should ensure that their changes are thoroughly tested to validate the integration of these underlying libraries and the overall functionality of the project.

1. **Integration Testing:**  
   Since our project is inherently a wrapper, integration tests are fundamental to verify that all components and dependencies interact correctly. These tests should cover the interaction between the wrapper and the low-level libraries it integrates with, ensuring that any changes or updates do not break existing functionality.

2. **End-to-End (E2E) Testing:**  
   We encourage contributors to develop E2E tests that demonstrate the proof of concept (PoC) for new functionalities. These tests should mimic real-world use cases and, where possible, be included as examples within the project. The aim is to validate that the new features work as intended from start to finish.

3. **Additional Tests:**  
   We welcome any additional testing methods (e.g., unit testing, regression testing, functional testing, black-box testing) that contributors deem necessary for ensuring the robustness and reliability of their contributions. Please provide the tests you have used, along with documentation explaining their purpose and expected outcomes.

For more inspiration on best practices across different applications, languages, and platforms, please refer to [testing practices on GitHub](https://github.com/topics/testing-practices).

## Submitting Code Pull Requests

We encourage and support contributions from the community. No fix is too small. We strive to process all pull requests as soon as possible and with constructive feedback. If your pull request is not accepted at first, please try again after addressing the feedback you received.

To make a pull request, you will need a GitHub account. For help, see GitHub's documentation on forking and pull requests.

All pull requests with code should include tests that validate your change.

## Developer's Certificate of Origin

All contributions must include acceptance of the DCO:

> Developer Certificate of Origin Version 1.1
>
> Copyright (C) 2004, 2006 The Linux Foundation and its contributors. 660
> York Street, Suite 102, San Francisco, CA 94110 USA
>
> Everyone is permitted to copy and distribute verbatim copies of this
> license document, but changing it is not allowed.
>
> Developer's Certificate of Origin 1.1
>
> By making a contribution to this project, I certify that:
>
> \(a) The contribution was created in whole or in part by me and I have
> the right to submit it under the open source license indicated in the
> file; or
>
> \(b) The contribution is based upon previous work that, to the best of my
> knowledge, is covered under an appropriate open source license and I
> have the right under that license to submit that work with
> modifications, whether created in whole or in part by me, under the same
> open source license (unless I am permitted to submit under a different
> license), as indicated in the file; or
>
> \(c) The contribution was provided directly to me by some other person
> who certified (a), (b) or (c) and I have not modified it.
>
> \(d) I understand and agree that this project and the contribution are
> public and that a record of the contribution (including all personal
> information I submit with it, including my sign-off) is maintained
> indefinitely and may be redistributed consistent with this project or
> the open source license(s) involved.

## Sign your work

To accept the DCO, simply add this line to each commit message with your name and email address (*git commit -s* will do this for you):

    Signed-off-by: Jane Example <jane@example.com>

For legal reasons, no anonymous or pseudonymous contributions are accepted.

## Other Ways to Contribute

If you don't feel like creating design assets or writing code, you can still contribute!

1. You may submit updates and improvements to the documentation.
2. Submit articles and guides which are also part of the documentation.
3. Help answer questions on StackOverflow, Slack and GitHub.

## References

This contribution guide was inspired by the contribution guides for [Grommet](https://github.com/grommet/grommet/blob/master/CONTRIBUTING.md) and [CloudSlang](http://www.cloudslang.io/#/docs#contributing-code).
