#!/usr/bin/env python3
"""
이메일 템플릿 및 수신자 그룹 시스템 예제 스크립트
"""

from email_notifier import EmailNotifier, EmailAuth
from email_template_manager import RecipientGroupManager
from web_crawler import WebCrawler, ExcelExporter
from pathlib import Path


def example_1_template_based_crawling_report():
    """예제 1: 템플릿 기반 크롤링 리포트 전송"""
    print("\n" + "=" * 60)
    print("예제 1: 템플릿 기반 크롤링 리포트 전송")
    print("=" * 60)

    # 이메일 초기화
    auth = EmailAuth()

    if not auth.is_configured():
        print("❌ 이메일이 설정되지 않았습니다. 먼저 설정을 완료해주세요.")
        return

    notifier = EmailNotifier(auth, use_templates=True)

    # 크롤러 초기화
    crawler = WebCrawler(use_cache=True)
    exporter = ExcelExporter()

    keyword = "파이썬"
    print(f"\n🔍 '{keyword}' 검색 중...")

    try:
        # 크롤링
        data = crawler.search_google_news(keyword, max_results=10)

        if data:
            # Excel 저장
            excel_file = f"{keyword}_template_result.xlsx"
            exporter.save_to_excel(data, excel_file, "뉴스")

            # 템플릿 기반 이메일 전송
            print(f"\n📧 템플릿 기반 이메일 전송 중...")
            success = notifier.send_crawling_report_with_template(
                to_email=auth.get_email(),
                keyword=keyword,
                data=data,
                excel_file=excel_file,
                search_type="Google News",
                show_preview=True
            )

            if success:
                print("✅ 템플릿 기반 이메일 전송 성공!")
            else:
                print("❌ 이메일 전송 실패")

            # 테스트 파일 삭제
            if Path(excel_file).exists():
                Path(excel_file).unlink()

        else:
            print("❌ 데이터 수집 실패")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")

    crawler.close()


def example_2_manage_recipient_groups():
    """예제 2: 수신자 그룹 관리"""
    print("\n" + "=" * 60)
    print("예제 2: 수신자 그룹 관리")
    print("=" * 60)

    auth = EmailAuth()
    notifier = EmailNotifier(auth)

    # 그룹 관리자 가져오기
    group_manager = notifier.get_recipient_manager()

    # 현재 그룹 리스트 조회
    print("\n📋 현재 그룹 리스트:")
    groups = notifier.list_recipient_groups()
    for group in groups:
        info = group_manager.get_group_info(group)
        recipients = group_manager.get_group_recipients(group)
        print(f"  📁 {group}: {info['name']}")
        print(f"     설명: {info['description']}")
        print(f"     수신자: {len(recipients)}명")
        if recipients:
            for r in recipients:
                print(f"       - {r}")

    # 새 그룹 생성 예시
    print("\n➕ 새 그룹 생성 예시")
    group_name = input("생성할 그룹 ID를 입력하세요 (영문, 예: sales): ").strip()

    if group_name:
        group_name_kr = input("그룹 이름을 입력하세요 (예: 영업팀): ").strip()
        description = input("그룹 설명을 입력하세요: ").strip()

        success = notifier.create_recipient_group(
            group_name=group_name,
            name=group_name_kr,
            description=description
        )

        if success:
            print(f"✅ 그룹 '{group_name_kr}' 생성 성공!")

            # 수신자 추가
            add_recipients = input("수신자를 추가하시겠습니까? (y/n): ").strip().lower()
            if add_recipients == 'y':
                while True:
                    email = input("수신자 이메일을 입력하세요 (엔터: 종료): ").strip()
                    if not email:
                        break
                    if notifier.add_recipient_to_group(group_name, email):
                        print(f"✅ {email} 추가 성공")
                    else:
                        print(f"❌ {email} 추가 실패")

            # 그룹 정보 확인
            recipients = group_manager.get_group_recipients(group_name)
            print(f"\n📋 그룹 '{group_name_kr}' 수신자 리스트 ({len(recipients)}명):")
            for r in recipients:
                print(f"  - {r}")
        else:
            print("❌ 그룹 생성 실패 (이미 존재하거나 오류 발생)")


def example_3_bulk_email_sending():
    """예제 3: 대량 이메일 발송"""
    print("\n" + "=" * 60)
    print("예제 3: 대량 이메일 발송")
    print("=" * 60)

    auth = EmailAuth()

    if not auth.is_configured():
        print("❌ 이메일이 설정되지 않았습니다.")
        return

    notifier = EmailNotifier(auth, use_templates=True)

    # 수신자 리스트 입력
    print("\n📧 대량 이메일 발송")
    print("수신자 이메일을 입력하세요. (한 줄에 하나씩, 빈 줄 입력 시 완료)")

    recipients = []
    while True:
        email = input("이메일: ").strip()
        if not email:
            break
        recipients.append(email)

    if not recipients:
        print("❌ 수신자가 없습니다.")
        return

    print(f"\n총 {len(recipients)}명에게 이메일을 발송합니다.")

    # 이메일 내용 입력
    subject = input("\n이메일 제목: ").strip()
    print("이메일 본문을 입력하세요. (빈 줄 입력 시 완료)")

    body_lines = []
    while True:
        line = input()
        if not line:
            break
        body_lines.append(line)

    body = "<br>".join(body_lines)

    # 지연 시간 설정
    delay_input = input("\n전송 지연 시간 (초, 기본값 2): ").strip()
    delay = float(delay_input) if delay_input else 2.0

    # 대량 발송
    print(f"\n📧 대량 이메일 발송 시작... (지연: {delay}초)")

    results = notifier.send_bulk_email(
        recipients=recipients,
        subject=subject,
        body=f"<h2>{subject}</h2><p>{body}</p>",
        is_html=True,
        delay=delay
    )

    # 결과 요약
    print("\n📊 발송 결과:")
    success_count = 0
    for email, success in results.items():
        status = "✅ 성공" if success else "❌ 실패"
        print(f"  {status}: {email}")
        if success:
            success_count += 1

    print(f"\n총계: {success_count}/{len(recipients)} 성공")


def example_4_group_email_sending():
    """예제 4: 그룹에 이메일 발송"""
    print("\n" + "=" * 60)
    print("예제 4: 그룹에 이메일 발송")
    print("=" * 60)

    auth = EmailAuth()

    if not auth.is_configured():
        print("❌ 이메일이 설정되지 않았습니다.")
        return

    notifier = EmailNotifier(auth, use_templates=True)

    # 그룹 선택
    print("\n📋 수신자 그룹:")
    groups = notifier.list_recipient_groups()

    for idx, group in enumerate(groups, 1):
        info = notifier.get_recipient_manager().get_group_info(group)
        recipients = notifier.get_recipient_manager().get_group_recipients(group)
        print(f"{idx}. {group}: {info['name']} ({len(recipients)}명)")

    choice = input(f"\n그룹을 선택하세요 (1-{len(groups)}): ").strip()

    try:
        group_idx = int(choice) - 1
        if 0 <= group_idx < len(groups):
            selected_group = groups[group_idx]

            # 그룹 정보 확인
            recipients = notifier.get_recipient_manager().get_group_recipients(selected_group)
            print(f"\n선택된 그룹: {selected_group}")
            print(f"수신자 수: {len(recipients)}명")

            if not recipients:
                print("❌ 그룹에 수신자가 없습니다.")
                return

            # 이메일 내용 입력
            subject = input("\n이메일 제목: ").strip()
            print("이메일 본문을 입력하세요. (빈 줄 입력 시 완료)")

            body_lines = []
            while True:
                line = input()
                if not line:
                    break
                body_lines.append(line)

            body = "<br>".join(body_lines)

            # 그룹에 발송
            print(f"\n📧 그룹 '{selected_group}'에 이메일 발송 중...")

            results = notifier.send_email_to_group(
                group_name=selected_group,
                subject=subject,
                body=f"<h2>{subject}</h2><p>{body}</p>",
                is_html=True,
                delay=2.0
            )

            # 결과 요약
            print("\n📊 발송 결과:")
            success_count = 0
            for email, success in results.items():
                status = "✅ 성공" if success else "❌ 실패"
                print(f"  {status}: {email}")
                if success:
                    success_count += 1

            print(f"\n총계: {success_count}/{len(recipients)} 성공")
        else:
            print("❌ 잘못된 선택입니다.")
    except ValueError:
        print("❌ 숫자를 입력해주세요.")


def example_5_custom_email_template():
    """예제 5: 사용자 정의 이메일 템플릿"""
    print("\n" + "=" * 60)
    print("예제 5: 사용자 정의 이메일 템플릿")
    print("=" * 60)

    auth = EmailAuth()

    if not auth.is_configured():
        print("❌ 이메일이 설정되지 않았습니다.")
        return

    notifier = EmailNotifier(auth, use_templates=True)

    # 이메일 정보 입력
    title = input("이메일 제목: ").strip()
    subject = input("이메일 메일 제목 (Subject): ").strip()

    print("아이콘을 선택하세요:")
    print("1. 📧 (기본)")
    print("2. 📊 (보고서)")
    print("3. 🎉 (축하)")
    print("4. ⚠️  (경고)")
    print("5. ✅ (성공)")
    print("6. 직접 입력")

    icon_choice = input("선택 (1-6): ").strip()
    icons = {"1": "📧", "2": "📊", "3": "🎉", "4": "⚠️", "5": "✅"}
    icon = icons.get(icon_choice, "📧")

    if icon_choice == "6":
        icon = input("아이콘 (이모지): ").strip()

    subtitle = input("부제목 (선택, 엔터 시 건너뜀): ").strip()
    footer_text = input("푸터 텍스트 (선택, 엔터 시 건너뜀): ").strip()

    print("\n이메일 본문을 입력하세요. (HTML 지원, 빈 줄 입력 시 완료)")
    body_lines = []
    while True:
        line = input()
        if not line:
            break
        body_lines.append(line)

    content = "<br>".join(body_lines)

    # 수신자 입력
    recipient = input("\n수신자 이메일: ").strip()

    if not recipient:
        recipient = auth.get_email()

    # 사용자 정의 이메일 전송
    print(f"\n📧 사용자 정의 이메일 전송 중...")

    success = notifier.send_custom_email_with_template(
        to_email=recipient,
        subject=subject,
        title=title,
        content=content,
        icon=icon,
        subtitle=subtitle,
        footer_text=footer_text
    )

    if success:
        print("✅ 사용자 정의 이메일 전송 성공!")
    else:
        print("❌ 이메일 전송 실패")


def main():
    """메인 메뉴"""
    print("\n🎨 이메일 템플릿 및 수신자 그룹 시스템 예제")
    print("=" * 60)

    examples = [
        ("템플릿 기반 크롤링 리포트 전송", example_1_template_based_crawling_report),
        ("수신자 그룹 관리", example_2_manage_recipient_groups),
        ("대량 이메일 발송", example_3_bulk_email_sending),
        ("그룹에 이메일 발송", example_4_group_email_sending),
        ("사용자 정의 이메일 템플릿", example_5_custom_email_template),
    ]

    print("\n실행할 예제를 선택하세요:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"{i}. {name}")

    print("0. 종료")

    try:
        choice = input("\n선택 (0-{}): ".format(len(examples))).strip()

        if choice == "0":
            print("종료합니다.")
        else:
            idx = int(choice) - 1
            if 0 <= idx < len(examples):
                name, func = examples[idx]
                try:
                    func()
                except Exception as e:
                    print(f"❌ 오류 발생: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print("잘못된 선택입니다.")

    except ValueError:
        print("잘못된 입력입니다.")
    except KeyboardInterrupt:
        print("\n\n사용자가 종료했습니다.")

    print("\n" + "=" * 60)
    print("✅ 예제 실행 완료!")
    print("=" * 60)


if __name__ == "__main__":
    main()
