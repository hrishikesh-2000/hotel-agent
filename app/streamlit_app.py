import time
import asyncio
import pandas as pd
import streamlit as st
from hotel_agent.pipeline import build_search_plan, ingest_bronze_pages, extract_silver_entities

st.set_page_config(page_title="Medallion Villa Scout | Agentic ETL", page_icon="⚡", layout="wide")

st.title("⚡ Autonomous Villa & Hotel Scout")
st.caption("Medallion Architecture (Plan → Bronze Parallel Scrape → Silver Entity Resolution → Gold Analytics)")

with st.sidebar:
    st.header("🎯 Search Parameters")
    destination = st.text_input("Destination City / Region", value="Mumbai")
    adults = st.number_input("Group Size (Adults)", min_value=1, max_value=40, value=8)
    amenities = st.text_area("Required Amenities", value="private pool, lawn, good view")
    
    st.divider()
    st.subheader("⚙️ Pipeline Controls")
    strict_geo = st.toggle(
        "Strict City Boundaries",
        value=True,
        help="When ON, blocks nearby outstation towns (e.g. drops Alibaug/Lonavala when searching Mumbai)."
    )
    max_urls = st.slider("Max Bronze Pages to Scrape", min_value=6, max_value=20, value=12, step=2)
    run_btn = st.button("🚀 Run Agentic Pipeline", type="primary", use_container_width=True)

async def execute_medallion_pipeline(dest, guests, reqs, strict, url_limit, status_box):
    t0 = time.perf_counter()

    # Stage 1: Planner
    status_box.write("🧠 **Stage 1 (Planner):** Resolving micro-localities & exclusion zones...")
    plan = await build_search_plan(dest, guests, reqs, strict)
    status_box.write(f"✅ **Target Pockets:** `{', '.join(plan.target_micro_localities)}`")
    if strict and plan.excluded_regions:
        status_box.write(f"🛡️ **Exclusion Guardrail:** `{', '.join(plan.excluded_regions)}`")

    # Stage 2: Bronze Ingestion
    status_box.write(f"⚡ **Stage 2 (Bronze):** Firing {len(plan.search_queries)} multi-portal queries & scraping up to {url_limit} URLs concurrently...")
    pages = await ingest_bronze_pages(plan.search_queries, max_urls=url_limit)
    status_box.write(f"📥 **Ingested:** `{len(pages)}` clean HTML documents into Bronze buffer.")

    # Stage 3: Silver Extraction & Filtering
    status_box.write("🔬 **Stage 3 (Silver):** Extracting all candidate entities, normalizing prices & enforcing geo-filters...")
    villas = await extract_silver_entities(pages, dest, guests, reqs, plan, strict)

    elapsed = round(time.perf_counter() - t0, 1)
    return plan, pages, villas, elapsed

if run_btn:
    status_ui = st.status("Executing Medallion Agent Pipeline...", expanded=True)
    plan, bronze_pages, silver_villas, duration = asyncio.run(
        execute_medallion_pipeline(destination, adults, amenities, strict_geo, max_urls, status_ui)
    )
    status_ui.update(label=f"Pipeline completed in {duration}s — Found {len(silver_villas)} verified properties", state="complete", expanded=False)

    # --- Telemetry KPI Row ---
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Multi-Portal Queries", len(plan.search_queries))
    m2.metric("Bronze Pages Scraped", len(bronze_pages))
    m3.metric("Verified Properties (Silver)", len(silver_villas))
    m4.metric("Pipeline Latency", f"{duration}s")

    with st.expander("🔍 Inspect Query Plan & Geographic Guardrails"):
        st.write("**Targeted Micro-Localities:**", ", ".join(plan.target_micro_localities))
        st.write("**Excluded Outstation Towns:**", ", ".join(plan.excluded_regions) if strict_geo else "None (Flexible Mode)")
        st.write("**Generated Search Queries:**")
        for q in plan.search_queries:
            st.code(q, language="text")

    if not silver_villas:
        st.warning("No properties passed the strict filter criteria. Try turning off 'Strict City Boundaries' or increasing 'Max Bronze Pages'.")
    else:
        tab1, tab2 = st.tabs(["📊 Gold Comparison Matrix (Table)", "🏡 Property Cards Grid"])

        # Prepare DataFrame for Analytical Table
        rows = []
        for v in silver_villas:
            per_person = f"₹{int(v.price_numeric / adults):,}" if v.price_numeric else "—"
            pool_label = "✅" if v.private_pool == "yes" else "❓" if v.private_pool == "unknown" else "❌"
            rows.append({
                "Property Name": v.name,
                "Micro-Locality": v.micro_locality,
                "City": v.city,
                "Source": v.source_domain,
                "Max Guests": v.capacity or "—",
                "Nightly Price": v.price_display,
                f"Per Person ({adults}p)": per_person,
                "Private Pool": pool_label,
                "Match Score": v.match_score,
                "Key Amenities": ", ".join(v.amenities[:4]),
                "Booking Link": v.booking_url,
            })
        df = pd.DataFrame(rows)

        with tab1:
            st.dataframe(
                df,
                column_config={
                    "Match Score": st.column_config.ProgressColumn("Match Score", min_value=0, max_value=100, format="%d%%"),
                    "Booking Link": st.column_config.LinkColumn("Booking Link", display_text="Open Listing ↗"),
                },
                use_container_width=True,
                hide_index=True,
            )
            csv_data = df.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Export Gold Dataset (CSV)", data=csv_data, file_name=f"{destination.lower()}_villas.csv", mime="text/csv")

        with tab2:
            cols = st.columns(3)
            for idx, v in enumerate(silver_villas):
                with cols[idx % 3]:
                    with st.container(border=True):
                        st.markdown(f"#### {v.name}")
                        st.caption(f"📍 **{v.micro_locality}** ({v.city})  |  🌐 `{v.source_domain}`")
                        
                        c1, c2 = st.columns(2)
                        c1.markdown(f"**Price:** `{v.price_display}`")
                        if v.price_numeric:
                            c2.markdown(f"**Split:** `₹{int(v.price_numeric / adults):,}/pp`")
                        else:
                            c2.markdown(f"**Guests:** `{v.capacity or 'N/A'}`")

                        pool_label = "✅ Yes" if v.private_pool == "yes" else "❓ Unknown" if v.private_pool == "unknown" else "❌ No"
                        st.markdown(f"🏊 **Pool:** {pool_label}  •  🎯 **Match:** `{v.match_score}%`")
                        st.write(v.summary)
                        if v.amenities:
                            st.caption(" • ".join(v.amenities[:5]))
                        st.link_button("View Listing ↗", v.booking_url, use_container_width=True)
