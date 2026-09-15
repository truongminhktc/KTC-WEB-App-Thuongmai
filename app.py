# ---------------------------------------------------------
    # TAB 3: XU HƯỚNG TĂNG TRƯỜNG (LOẠI BỎ CHỮ 'B' TRÊN TRỤC Y)
    # ---------------------------------------------------------
    with tab3:
        st.markdown("##### 📈 Biến Động Chu Kỳ Tăng Trưởng - Top Sản Phẩm Chủ Lực")
        
        top5_skus = df_filtered.groupby('Ten_SP')[unit_choice].sum().nlargest(5).index.tolist()
        selected_display_skus = st.multiselect("Tùy chọn danh mục sản phẩm theo dõi:", options=df_filtered['Ten_SP'].unique(), default=top5_skus)

        trend_df = df_filtered[df_filtered['Ten_SP'].isin(selected_display_skus)].groupby(['Thang', 'Ten_SP'])[unit_choice].sum().reset_index()

        if not trend_df.empty:
            # Quy đổi dữ liệu để khử chữ 'B' của hệ thống Mỹ
            if unit_choice == 'Doanh_Thu':
                trend_df['Gia_Tri_Hien_Thi'] = trend_df[unit_choice] / 1e9
                y_label = "Doanh Thu (Tỷ VNĐ)"
                hover_suffix = " Tỷ"
            else:
                trend_df['Gia_Tri_Hien_Thi'] = trend_df[unit_choice]
                y_label = "Sản Lượng (Bao)"
                hover_suffix = " Bao"

            fig_line = px.line(
                trend_df, x='Thang', y='Gia_Tri_Hien_Thi', color='Ten_SP', markers=True,
                color_discrete_sequence=EXECUTIVE_PALETTE,
                labels={'Gia_Tri_Hien_Thi': y_label, 'Ten_SP': 'Sản phẩm'}
            )
            
            fig_line.update_traces(
                line=dict(width=3), 
                marker=dict(size=8, symbol='circle'),
                hovertemplate='<b>%{x}</b><br>%{data.name}<br>Giá trị: <b>%{y:,.1f}</b>' + hover_suffix
            )
            
            layout_trend = DARK_LAYOUT.copy()
            layout_trend['margin'] = dict(l=20, r=20, t=60, b=50)
            fig_line.update_layout(
                **layout_trend, 
                height=450, 
                legend=dict(
                    orientation="h", 
                    yanchor="bottom", 
                    y=1.12, 
                    xanchor="left", 
                    x=0, 
                    title_text="",
                    font=dict(size=11) # Thu nhỏ font nhãn sản phẩm để không bị tràn màn hình
                ),
                xaxis_title="",
                yaxis=dict(
                    title=y_label, 
                    showgrid=True, 
                    gridcolor='rgba(255,255,255,0.06)',
                    tickformat=".1f" # Ép định dạng số chuẩn
                )
            )
            st.plotly_chart(fig_line, use_container_width=True)

    # ---------------------------------------------------------
    # TAB 4: NĂNG LỰC & RỦI RO NPP (ẨN TRỤC X DƯ THỪA, LOẠI BỎ CHỮ 'B')
    # ---------------------------------------------------------
    with tab4:
        st.markdown("##### 🏆 Top 15 Nhà Phân Phối Đóng Góp Lớn Nhất")
        
        npp_df = df_filtered.groupby('Thuyet_Minh_NPP')[unit_choice].sum().reset_index()
        npp_df = npp_df.sort_values(by=unit_choice, ascending=True).tail(15)

        # Tính toán giá trị hiển thị thực tế
        if unit_choice == 'Doanh_Thu':
            npp_df['Gia_Tri_Hien_Thi'] = npp_df[unit_choice] / 1e9
            npp_df['Val_Label'] = npp_df['Gia_Tri_Hien_Thi'].apply(lambda x: f"{x:,.1f} Tỷ")
        else:
            npp_df['Gia_Tri_Hien_Thi'] = npp_df[unit_choice]
            npp_df['Val_Label'] = npp_df['Gia_Tri_Hien_Thi'].apply(lambda x: f"{x:,.0f} Bao")

        npp_df['Short_Name'] = npp_df['Thuyet_Minh_NPP'].apply(lambda x: x[:38] + '...' if len(x) > 38 else x)

        if not npp_df.empty:
            fig_npp = px.bar(
                npp_df, x='Gia_Tri_Hien_Thi', y='Short_Name', orientation='h',
                text='Val_Label',
                hover_name='Thuyet_Minh_NPP'
            )
            
            fig_npp.update_traces(
                marker_color='#38bdf8', 
                marker_line=dict(width=1, color='rgba(255,255,255,0.2)'),
                textposition='outside',
                textfont=dict(color='#cbd5e1', size=11, family="Plus Jakarta Sans"),
                hovertemplate='<b>%{hovertext}</b><br>Đóng góp: <b>%{text}</b>'
            )
            
            layout_npp = DARK_LAYOUT.copy()
            layout_npp['margin'] = dict(l=20, r=80, t=20, b=30)
            
            fig_npp.update_layout(
                **layout_npp, 
                height=480, 
                yaxis_title="", 
                # Ẩn hoàn toàn trục X vì đã có nhãn text đính kèm ngay trên cột
                xaxis=dict(showticklabels=False, showgrid=False, title="", zeroline=False)
            )
            st.plotly_chart(fig_npp, use_container_width=True)

            st.markdown("##### ⚠️ Phân Tích Mức Độ Tập Trung & Rủi Ro Phụ Thuộc (Pareto NPP):")
            st.info(f"Top 3 NPP đóng góp {top3_npp_pct:.1f}% tổng doanh số. Cần đảm bảo hạn mức tín dụng công nợ trong tầm kiểm soát.")
