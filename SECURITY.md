# Security Release Process

[Athon/LLM Agentic Tool Mesh] is a  growing community devoted in creating [democratizing Generative Artificial Intelligence (Gen AI)]. The community has adopted this security disclosure and response policy to ensure we responsibly handle critical issues.

## Supported Versions

The [Athon/LLM Agentic Tool Mesh] project maintains release branches for the three most recent minor releases. Applicable fixes, including security fixes, may be backported to those three release branches, depending on severity and feasibility. Please refer to [README.md](README.md) for details.

## Reporting a Vulnerability - Private Disclosure Process

Security is of the highest importance and all security vulnerabilities or suspected security vulnerabilities should be reported to [Athon/LLM Agentic Tool Mesh] privately, to minimize attacks against current users of [Athon/LLM Agentic Tool Mesh] before they are fixed. Vulnerabilities will be investigated and patched on the next patch (or minor) release as soon as possible. This information could be kept entirely internal to the project.  

If you know of a publicly disclosed security vulnerability for [Athon/LLM Agentic Tool Mesh], please **IMMEDIATELY** contact <github@hpe.com> to inform the [Athon/LLM Agentic Tool Mesh] Security Team.

IMPORTANT: Do not file public issues on GitHub for security vulnerabilities

### Proposed Email Content

Provide a descriptive subject line and in the body of the email include the following information:

* Basic identity information, such as your name and your affiliation or company.
* Type of issue (e.g. buffer overflow, SQL injection, cross-site scripting, etc.)
* Full paths of source file(s) related to the manifestation of the issue
* The location of the affected source code (tag/branch/commit or direct URL)
* Any special configuration required to reproduce the issue
* Detailed steps to reproduce the vulnerability  (POC scripts, screenshots, and compressed packet captures are all helpful to us).
* Proof-of-concept or exploit code (if possible)
* Impact of the issue, including how an attacker might exploit the issue
* Description of the effects of the vulnerability on [Athon/LLM Agentic Tool Mesh] and the related hardware and software configurations, so that the [Athon/LLM Agentic Tool Mesh] Security Team can reproduce it.
* How the vulnerability affects [Athon/LLM Agentic Tool Mesh] usage and an estimation of the attack surface, if there is one.
* List other projects or dependencies that were used in conjunction with [Athon/LLM Agentic Tool Mesh] to produce the vulnerability.

This information will help us triage your report more quickly.

**Please provide as much information as possible from above, but notify <github@hpe.com> as soon as possible even if some of the information cannot be immediately provided.**

## When to report a vulnerability

* When you think [Athon/LLM Agentic Tool Mesh] has a potential security vulnerability.
* When you suspect a potential vulnerability, but you are unsure that it impacts [Athon/LLM Agentic Tool Mesh].
* When you know of or suspect a potential vulnerability on another project that is used by [Athon/LLM Agentic Tool Mesh. For example [Athon/LLM Agentic Tool Mesh] has a dependency on [Langchain](https://github.com/langchain-ai/langchain), etc.
  
## Patch, Release, and Disclosure

The [Athon/LLM Agentic Tool Mesh] Security Team will respond to vulnerability reports as follows:

1. The Security Team will investigate the vulnerability and determine its effects and criticality.
2. If the issue is not deemed to be a vulnerability, the Security Team will follow up with a detailed reason for rejection.
3. The Security Team will initiate a conversation with the reporter on the order of 5 business days.
4. If a vulnerability is acknowledged and the timeline for a fix is determined, the Security Team will work on a plan to communicate with the appropriate community, including identifying mitigating steps that affected users can take to protect themselves until the fix is rolled out.
5. The Security Team will work on fixing the vulnerability and perform internal testing before preparing to roll out the fix.
6. The Security Team will provide early disclosure of the vulnerability by emailing the security mailing list. Distributors can initially plan for the vulnerability patch ahead of the fix, and later can test the fix and provide feedback to the [Athon/LLM Agentic Tool Mesh] team. See the section **Early Disclosure to [Athon/LLM Agentic Tool Mesh] Distributors List** for details about how to join this mailing list.
7. A public disclosure date is negotiated by the [Athon/LLM Agentic Tool Mesh] Security Team, the bug submitter, and the distributors list. We prefer to fully disclose the bug as soon as possible once a user mitigation or patch is available. It is reasonable to delay disclosure when the bug or the fix is not yet fully understood, the solution is not well-tested, or for distributor coordination. The timeframe for disclosure is from immediate (especially if it’s already publicly known) to a few weeks. For a critical vulnerability with a straightforward mitigation, we expect report date to public disclosure date to be on the order of 14 business days. The [Athon/LLM Agentic Tool Mesh] Security Team holds the final say when setting a public disclosure date.
8. Once the fix is confirmed, the Security Team will patch the vulnerability in the next patch or minor release, and backport a patch release into all earlier supported releases. Upon release of the patched version of [Athon/LLM Agentic Tool Mesh], we will follow the **Public Disclosure Process**.

### Public Disclosure Process

The Security Team publishes a public [advisory] to the [Athon/LLM Agentic Tool Mesh] community via GitHub. In most cases, additional communication via Slack, security mailing lists, and other channels will assist in educating [Athon/LLM Agentic Tool Mesh] users and rolling out the patched release to affected users.

The Security Team will also publish any mitigating steps users can take until the fix can be applied to their [Athon/LLM Agentic Tool Mesh] instances. [Athon/LLM Agentic Tool Mesh] distributors will handle creating and publishing their own security advisories.

## Mailing lists

* Use <github@hpe.com> to report security concerns to the [Athon/LLM Agentic Tool Mesh] Security Team, who uses the list to privately discuss security issues and fixes prior to disclosure.
* Join security mailing list for early private information and vulnerability disclosure. Early disclosure may include mitigating steps and additional information on security patch releases. See below for information on how [Athon/LLM Agentic Tool Mesh] distributors or vendors can apply to join this list.

## Early Disclosure to [Athon/LLM Agentic Tool Mesh] Distributors List

This private list is intended to be used primarily to provide actionable information to multiple distributor projects at once. This list is not intended to inform individuals about security issues.

### Membership Criteria

To be eligible to join the security mailing list, you should:

1. Be an active distributor of [Athon/LLM Agentic Tool Mesh].
2. Have a user base that is not limited to your own organization. **[ maybe remove this... ]**
3. Have a publicly verifiable track record up to the present day of fixing security issues.
4. Not be a downstream or rebuild of another distributor.
5. Be a participant and active contributor in the [Athon/LLM Agentic Tool Mesh] community.
6. Accept the Embargo Policy that is outlined below.
7. Has someone who is already on the list vouch for the person requesting membership on behalf of your distribution.

The terms and conditions of the Embargo Policy apply to all members of this mailing list. A request for membership represents your acceptance to the terms and conditions of the Embargo Policy

### Embargo Policy

The information that members receive on security mailing list must not be made public, shared, or even hinted at anywhere beyond those who need to know within your specific team, unless you receive explicit approval to do so from the [Athon/LLM Agentic Tool Mesh] Security Team. This remains true until the public disclosure date/time agreed upon by the list. Members of the list and others cannot use the information for any reason other than to get the issue fixed for your respective distribution's users.
Before you share any information from the list with members of your team who are required to fix the issue, these team members must agree to the same terms, and only be provided with information on a need-to-know basis.

In the unfortunate event that you share information beyond what is permitted by this policy, you must urgently inform the security mailing list of exactly what information was leaked and to whom. If you continue to leak information and break the policy outlined here, you will be permanently removed from the list.

### Requesting to Join

Send new membership requests to <github@hpe.com>
In the body of your request please specify how you qualify for membership and fulfill each criterion listed in the Membership Criteria section above.

## Confidentiality, integrity and availability

We consider vulnerabilities leading to the compromise of data confidentiality, elevation of privilege, or integrity to be our highest priority concerns. Availability, in particular in areas relating to DoS and resource exhaustion, is also a serious security concern. The [Athon/LLM Agentic Tool Mesh] Security Team takes all vulnerabilities, potential vulnerabilities, and suspected vulnerabilities seriously and will investigate them in an urgent and expeditious manner.

Note that we do not currently consider the default settings for [Athon/LLM Agentic Tool Mesh] to be secure-by-default. It is necessary for operators to explicitly configure settings, role based access control, and other resource related features in [Athon/LLM Agentic Tool Mesh] to provide a hardened [Athon/LLM Agentic Tool Mesh] environment.

## Preferred Languages

We prefer all communications to be in English.

## Policy

Under the principle of Coordinated Vulnerability Disclosure, researchers disclose newly discovered vulnerabilities in hardware, software, and services directly to the vendors of the affected product; to a national CERT or other coordinator who will report to the vendor privately; or to a private service that will likewise report to the vendor privately. The researcher allows the vendor the opportunity to diagnose and offer fully tested updates, workarounds, or other corrective measures before any party discloses detailed vulnerability or exploit information to the public. The vendor continues to coordinate with the researcher throughout the vulnerability investigation and provides the researcher with updates on case progress. Upon release of an update, the vendor may recognize the finder for the research and privately reporting the issue. If attacks are underway in the wild, and the vendor is still working on the update, then both the researcher and vendor work together as closely as possible to provide early public vulnerability disclosure to protect customers. The aim is to provide timely and consistent guidance to customers to help them protect themselve*s.*

For more information on CVD, please review the information provided in the following links:

* [ISO/IEC 29147:2018 on Vulnerability Disclosure](https://www.iso.org/standard/72311.html)
* [The CERT Guide to Coordinated Vulnerability Disclosure](https://resources.sei.cmu.edu/asset_files/SpecialReport/2017_003_001_503340.pdf)
