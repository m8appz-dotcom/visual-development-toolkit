# Security reporting

Never include credentials, access tokens, private conversations, or personal data in a public issue or pull request.

For a sensitive report, establish a private contact route with the repository maintainer first. If no private route is available, open an issue requesting private contact and describe only the affected component, without exploit details or secrets. Do not assume that a private-reporting feature is enabled.

Reproduce issues in an isolated environment with authorized sample data. Preserve existing access and recovery methods when proposing an authentication change. See the documented checks and limitations in docs/DEMO.md; a passing offline suite is not a certification of a live deployment.
