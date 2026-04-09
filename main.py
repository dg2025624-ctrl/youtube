#!/usr/bin/env python3
"""
CLI 인터페이스 - 터미널에서 YouTube 댓글 분석
사용법: python cli.py <URL or video_id> [--max 500] [--order time] [--json]
"""

import argparse
import json
import os
import sys

from src.analyzer import YouTubeCommentAnalyzer


def main():
    parser = argparse.ArgumentParser(
        description="YouTube 댓글 분석기",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  python cli.py https://www.youtube.com/watch?v=dQw4w9WgXcQ
  python cli.py dQw4w9WgXcQ --max 1000 --order time
  python cli.py dQw4w9WgXcQ --json > result.json
        """,
    )
    parser.add_argument("url", help="YouTube URL 또는 video_id")
    parser.add_argument("--max", type=int, default=200, help="최대 댓글 수 (기본값: 200)")
    parser.add_argument(
        "--order",
        choices=["relevance", "time"],
        default="relevance",
        help="정렬 기준 (기본값: relevance)",
    )
    parser.add_argument("--json", action="store_true", help="JSON 형식으로 출력")
    parser.add_argument("--api-key", help="YouTube API 키 (환경변수 YOUTUBE_API_KEY 대체)")

    args = parser.parse_args()

    api_key = args.api_key or os.environ.get("YOUTUBE_API_KEY", "")
    if not api_key:
        print("❌ YouTube API 키가 필요합니다.", file=sys.stderr)
        print("   환경변수: export YOUTUBE_API_KEY=your_key", file=sys.stderr)
        print("   또는 --api-key 옵션 사용", file=sys.stderr)
        sys.exit(1)

    try:
        analyzer = YouTubeCommentAnalyzer(api_key)
        video_id = analyzer.extract_video_id(args.url)

        print(f"📹 동영상 정보 조회 중...", file=sys.stderr)
        video_info = analyzer.get_video_info(video_id)

        print(f"💬 댓글 수집 중 (최대 {args.max}개)...", file=sys.stderr)
        comments = analyzer.fetch_comments(video_id, max_comments=args.max, order=args.order)

        print(f"🔍 분석 중...\n", file=sys.stderr)
        analysis = analyzer.analyze(comments)

        if args.json:
            result = {"video_info": video_info, "analysis": analysis}
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return

        # ── 사람이 읽기 좋은 형식 출력 ──
        print("=" * 60)
        print(f"📺 {video_info['title']}")
        print(f"   채널: {video_info['channel']}")
        print(f"   조회수: {video_info['view_count']:,}")
        print(f"   좋아요: {video_info['like_count']:,}")
        print(f"   댓글 수: {video_info['comment_count']:,}")
        print("=" * 60)

        print(f"\n✅ 수집된 댓글: {analysis['total_comments']:,}개")

        stats = analysis["statistics"]
        print(f"\n📊 좋아요 통계")
        print(f"   평균: {stats['avg_likes']}")
        print(f"   중앙값: {stats['median_likes']}")
        print(f"   최대: {stats['max_likes']}")

        eng = analysis["engagement_rate"]
        print(f"\n💡 참여율")
        print(f"   좋아요 받은 댓글: {eng['liked_rate']}%")
        print(f"   답글 달린 댓글:   {eng['reply_rate']}%")

        print(f"\n🔤 자주 쓰인 단어 Top 15")
        for word, count in analysis["word_frequency"][:15]:
            bar = "█" * min(count, 30)
            print(f"   {word:<15} {bar} {count}")

        print(f"\n😀 자주 쓰인 이모지 Top 10")
        for emoji, count in analysis["emoji_frequency"][:10]:
            print(f"   {emoji}  {count}회")

        print(f"\n🏆 좋아요 Top 5 댓글")
        for i, c in enumerate(analysis["top_comments"][:5], 1):
            text = c["text_original"].replace("\n", " ")[:80]
            print(f"   {i}. ({c['like_count']}👍) {text}")

        print("\n" + "=" * 60)

    except (ValueError, PermissionError, EnvironmentError) as e:
        print(f"❌ {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n⏹ 중단되었습니다.", file=sys.stderr)
        sys.exit(0)


if __name__ == "__main__":
    main()
