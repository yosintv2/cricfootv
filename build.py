# Inside build.py ...

for i in range(7):
    day = START_WEEK + timedelta(days=i)
    fname = "index.html" if day == TODAY_DATE else f"{day.strftime('%Y-%m-%d')}.html"
    
    # --- DYNAMIC MENU FOR EACH PAGE ---
    current_page_menu = ""
    for j in range(7):
        menu_day = START_WEEK + timedelta(days=j)
        menu_fname = "index.html" if menu_day == TODAY_DATE else f"{menu_day.strftime('%Y-%m-%d')}.html"
        
        # This adds the "active" class ONLY to the button matching the current file
        active_class = "active" if menu_day == day else ""
        
        current_page_menu += f'<a href="{DOMAIN}/{menu_fname}" class="date-btn {active_class}"><div>{menu_day.strftime("%a")}</div><b>{menu_day.strftime("%b %d")}</b></a>'

    # Filter matches for the specific day
    day_matches = [m for m in all_matches if datetime.fromtimestamp(m['kickoff']).date() == day]
    
    # ... (rest of your listing_html generation logic) ...

    # Write the file with the custom menu and display date
    with open(fname, "w", encoding='utf-8') as df:
        output = templates['home'].replace("{{MATCH_LISTING}}", listing_html)
        output = output.replace("{{WEEKLY_MENU}}", current_page_menu) # Dynamic menu
        output = output.replace("{{DOMAIN}}", DOMAIN)
        output = output.replace("{{DISPLAY_DATE}}", day.strftime("%A, %B %d, %Y")) # Banner date
        output = output.replace("{{PAGE_TITLE}}", f"Soccer TV Schedule {day.strftime('%Y-%m-%d')}")
        df.write(output)
