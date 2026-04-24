from __future__ import annotations

import argparse

from textSummarizer.summarizer import summarize_text


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize user-provided text")
    parser.add_argument("text", type=str, help="Text to summarize")
    parser.add_argument("--max-length", type=int, default=130)
    parser.add_argument("--min-length", type=int, default=30)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.min_length >= args.max_length:
        raise ValueError("--min-length must be less than --max-length")

    summary = summarize_text(
        text=args.text,
        max_length=args.max_length,
        min_length=args.min_length,
        do_sample=False,
    )
    print(summary)


if __name__ == "__main__":
    main()
