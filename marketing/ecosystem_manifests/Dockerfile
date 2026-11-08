# DevSuperSuite Official Multi-Arch Container Image
# Compliance: 100% Brand Anonymity | Zero Telemetry | Offline Air-Gapped Execution
FROM alpine:3.20 AS builder

RUN apk add --no-cache ca-certificates curl

FROM alpine:3.20

LABEL maintainer="DevSuperSuite Ecosystem Engineering <ecosystem@devsupersuite.com>" \
      org.opencontainers.image.title="DevSuperSuite CLI" \
      org.opencontainers.image.description="Local-first AST context slicer & pre-commit entropy defense" \
      org.opencontainers.image.url="https://devsupersuite.web.app" \
      org.opencontainers.image.vendor="DevSuperSuite"

# Create unprivileged runtime user
RUN addgroup -S devsuper && adduser -S devsuper -G devsuper

# Copy statically linked binary
COPY devsupersuite /usr/local/bin/devsupersuite
RUN chmod +x /usr/local/bin/devsupersuite

USER devsuper
WORKDIR /workspace

ENTRYPOINT ["/usr/local/bin/devsupersuite"]
CMD ["--help"]
