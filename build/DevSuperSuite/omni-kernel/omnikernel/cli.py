"""
OmniKernel CLI: Command-line interface for context compression and invariant auditing.
"""

import sys
import argparse
from pathlib import Path
from omnikernel.compressor import ASTContextCompressor
from omnikernel.invariants import InvariantGuard


def main():
    parser = argparse.ArgumentParser(description="OmniKernel 5.0: Neural Context Compressor & Invariant Guard")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Compress command
    comp_parser = subparsers.add_parser("compress", help="Compress code file context")
    comp_parser.add_argument("file", help="Path to source file")
    comp_parser.add_argument("--out", "-o", help="Optional output path")

    # Audit command
    audit_parser = subparsers.add_parser("audit", help="Audit patch invariants")
    audit_parser.add_argument("original", help="Original source file")
    audit_parser.add_argument("patch", help="Proposed patched file")

    args = parser.parse_args()

    if args.command == "compress":
        p = Path(args.file)
        if not p.exists():
            print(f"Error: File not found: {args.file}", file=sys.stderr)
            sys.exit(1)
        
        content = p.read_text(encoding="utf-8", errors="ignore")
        compressor = ASTContextCompressor()
        if p.suffix == ".py":
            compressed, metrics = compressor.compress_python(content)
        else:
            compressed, metrics = compressor.compress_generic(content)

        if args.out:
            Path(args.out).write_text(compressed, encoding="utf-8")
            print(f"Compressed code written to {args.out}")
        else:
            print(compressed)

        print("\n" + "=" * 50, file=sys.stderr)
        print("OmniKernel 5.0 Compression Metrics:", file=sys.stderr)
        for k, v in metrics.items():
            print(f"  {k}: {v}", file=sys.stderr)
        print("=" * 50, file=sys.stderr)

    elif args.command == "audit":
        p1 = Path(args.original)
        p2 = Path(args.patch)
        res = InvariantGuard.audit_patch(p1.read_text(encoding="utf-8"), p2.read_text(encoding="utf-8"))
        print(f"Audit Status: {res['status']}")
        if res['violations']:
            for v in res['violations']:
                print(f"❌ [{v['severity']}] {v['rule']}: {v['message']}")
            sys.exit(1)
        else:
            print("✅ All architectural invariants satisfied.")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
