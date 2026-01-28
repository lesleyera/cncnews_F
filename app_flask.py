from __future__ import annotations

import os
from datetime import datetime

from flask import Flask, redirect, render_template, request, session, url_for

import config
import data
from utils import WEEK_MAP


def create_app() -> Flask:
    app = Flask(__name__)
    # 자체 서버 배포 시에는 환경변수로 꼭 바꾸세요.
    app.secret_key = os.getenv("FLASK_SECRET_KEY", "CHANGE_ME__PLEASE_SET_FLASK_SECRET_KEY")

    access_code = os.getenv("ACCESS_CODE", "cncnews2026")

    @app.get("/")
    def index():
        if not session.get("password_correct"):
            return redirect(url_for("login"))
        return redirect(url_for("dashboard"))

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if session.get("password_correct"):
            return redirect(url_for("dashboard"))

        error = None
        if request.method == "POST":
            password = (request.form.get("password") or "").strip()
            if password == access_code:
                session["password_correct"] = True
                return redirect(url_for("dashboard"))
            error = "코드가 올바르지 않습니다."

        return render_template(
            "login.html",
            css=config.CSS,
            error=error,
        )

    @app.post("/logout")
    def logout():
        session.clear()
        return redirect(url_for("login"))

    @app.get("/dashboard")
    def dashboard():
        if not session.get("password_correct"):
            return redirect(url_for("login"))

        selected_week = request.args.get("week")
        if selected_week not in WEEK_MAP:
            selected_week = list(WEEK_MAP.keys())[0]

        (
            cur_uv,
            cur_pv,
            df_daily,
            df_weekly,
            df_traffic_curr,
            df_traffic_last,
            df_region_curr,
            df_region_last,
            df_age_curr,
            df_age_last,
            df_gender_curr,
            df_gender_last,
            df_top10,
            _df_raw_all,
            new_ratio,
            search_ratio,
            active_article_count,
            df_top10_sources,
            published_article_count,
            df_all_articles_with_metadata,
        ) = data.load_all_dashboard_data(selected_week)

        writers_df = data.get_writers_df_real(df_all_articles_with_metadata)

        return render_template(
            "dashboard.html",
            css=config.CSS,
            print_css=config.PRINT_CSS,
            now=datetime.now(),
            week_map=WEEK_MAP,
            selected_week=selected_week,
            period=WEEK_MAP[selected_week],
            # 숫자/지표
            cur_uv=cur_uv,
            cur_pv=cur_pv,
            new_ratio=new_ratio,
            search_ratio=search_ratio,
            active_article_count=active_article_count,
            published_article_count=published_article_count,
            # 데이터(테이블/차트)
            df_daily=df_daily,
            df_weekly=df_weekly,
            df_traffic_curr=df_traffic_curr,
            df_traffic_last=df_traffic_last,
            df_region_curr=df_region_curr,
            df_region_last=df_region_last,
            df_age_curr=df_age_curr,
            df_age_last=df_age_last,
            df_gender_curr=df_gender_curr,
            df_gender_last=df_gender_last,
            df_top10=df_top10,
            df_top10_sources=df_top10_sources,
            writers_df=writers_df,
        )

    @app.get("/print")
    def print_view():
        if not session.get("password_correct"):
            return redirect(url_for("login"))

        selected_week = request.args.get("week")
        if selected_week not in WEEK_MAP:
            selected_week = list(WEEK_MAP.keys())[0]

        (
            cur_uv,
            cur_pv,
            df_daily,
            df_weekly,
            df_traffic_curr,
            df_traffic_last,
            df_region_curr,
            df_region_last,
            df_age_curr,
            df_age_last,
            df_gender_curr,
            df_gender_last,
            df_top10,
            _df_raw_all,
            new_ratio,
            search_ratio,
            active_article_count,
            df_top10_sources,
            published_article_count,
            df_all_articles_with_metadata,
        ) = data.load_all_dashboard_data(selected_week)

        writers_df = data.get_writers_df_real(df_all_articles_with_metadata)

        return render_template(
            "print.html",
            css=config.CSS,
            print_css=config.PRINT_CSS,
            now=datetime.now(),
            week_map=WEEK_MAP,
            selected_week=selected_week,
            period=WEEK_MAP[selected_week],
            cur_uv=cur_uv,
            cur_pv=cur_pv,
            new_ratio=new_ratio,
            search_ratio=search_ratio,
            active_article_count=active_article_count,
            published_article_count=published_article_count,
            df_daily=df_daily,
            df_weekly=df_weekly,
            df_traffic_curr=df_traffic_curr,
            df_traffic_last=df_traffic_last,
            df_region_curr=df_region_curr,
            df_region_last=df_region_last,
            df_age_curr=df_age_curr,
            df_age_last=df_age_last,
            df_gender_curr=df_gender_curr,
            df_gender_last=df_gender_last,
            df_top10=df_top10,
            df_top10_sources=df_top10_sources,
            writers_df=writers_df,
        )

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8000")), debug=True)

