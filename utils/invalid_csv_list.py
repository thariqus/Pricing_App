def reject_csv_list(lists, reason, raw):
    raw["reason"] = reason
    lists.append(raw)
    return lists