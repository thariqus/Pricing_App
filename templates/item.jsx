import { useEffect, useMemo, useRef, useState } from "react";
import {
  downloadCsv as saveCsvFile,
  rowsToCsv,
  fetchAllItemPrices,
  fromDbRow,
  createSingleItemPrice,
} from "../api";


import {
  FaSearch,
  FaDownload,
  FaFileImport,
  FaPlus,
} from "react-icons/fa";

// const UOM_OPTIONS = ["PAC", "EA", "CAR"];
const LOCATION_OPTIONS = ["2112", "2113", "2132"];
// const CURRENCY_OPTIONS = ["AED", "USD", "EUR", "GBP", "JPY", "CAD", "AUD"];
const PRIORITY_OPTIONS = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11"];

const COLUMNS = [
  { key: "active", label: "Active", type: "active", width: 45 },
  { key: "conditionType", label: "Condition Type", type: "text", width: 95 },
  { key: "itemNo", label: "Item No", type: "text", width: 80 },
  { key: "customer", label: "Customer", type: "text", width: 85 },
  { key: "customerGrp", label: "Customer Grp", type: "text", width: 85 },
  { key: "customerHierarchy", label: "Customer Hierarchy", type: "text", width: 95 },
  { key: "distributionChannel", label: "Distribution Channel", type: "text", width: 105 },
  { key: "locationCode", label: "Location Code", type: "select", options: LOCATION_OPTIONS, width: 90, editable: true },
  { key: "priority", label: "Priority", type: "select", options: PRIORITY_OPTIONS, width: 65, editable: true },
  // { key: "currency", label: "Currency", type: "select", options: CURRENCY_OPTIONS, width: 70, editable: true },
  { key: "currency", label: "Currency", type: "text", width: 70, editable: true },
  { key: "salesPrice", label: "Sales Price", type: "number", width: 80, editable: true },
  // { key: "uom", label: "UOM", type: "select", options: UOM_OPTIONS, width: 60, editable: true },
  { key: "uom", label: "UOM", type: "text", width: 60, editable: true },
  { key: "minQty", label: "Min Qty", type: "number", width: 65, editable: true },
  { key: "startingDate", label: "Starting Date", type: "datetime", width: 145, editable: true },
  { key: "endingDate", label: "Ending Date", type: "datetime", width: 145, editable: true },
  { key: "lowerLimit", label: "Lower Limit", type: "number", width: 80, editable: true },
  { key: "upperLimit", label: "Upper Limit", type: "number", width: 80, editable: true },
  { key: "zoneCode", label: "Zone Code", type: "text", width: 85, editable: true },
  { key: "offerArticle", label: "Offer Article", type: "text", width: 85, editable: true },
];

const FILTER_OPTIONS = [
  ["customer_group_hierarchy", "Customer / Group / Hierarchy"],
  ["sort_by", "Sort By"],
  ["salesOrganization", "Sales Organization"],
  ["distributionChannel", "Distribution Channel"],
  ["locationCode", "Location Code"],
  ["conditionType", "Condition Type"],
  ["salesPrice", "Sales Price"],
  ["currency", "Currency"],
  ["uom", "Unit of Measure"],
  ["minQty", "Minimum Quantity"],
  ["lowerLimit", "Lower Limit"],
  ["upperLimit", "Upper Limit"],
  ["zoneCode", "Transportation Zone"],
  ["startingDate", "Starting Date"],
  ["endingDate", "Ending Date"],
  ["priority", "Priority"],
  ["offerArticle", "Offer Article"],
];

const PRIORITY_CONFIG = [
  ["distributionChannel", "customer", "locationCode", "itemNo", "uom"],
  ["distributionChannel", "customerGrp", "locationCode", "itemNo", "uom"],
  ["distributionChannel", "customer", "itemNo", "uom"],
  ["distributionChannel", "customerGrp", "itemNo", "uom"],
  ["customerGrp", "itemNo", "uom"],
  ["customerHierarchy", "locationCode", "itemNo", "uom"],
  ["customerHierarchy", "itemNo", "uom"],
  ["distributionChannel", "locationCode", "itemNo", "zoneCode", "uom"],
  ["distributionChannel", "locationCode", "itemNo", "uom"],
  ["distributionChannel", "itemNo", "uom"],
  ["itemNo", "uom"],
];

const LABELS = {
  conditionType: "Condition Type",
  salesPrice: "Sales Price",
  startingDate: "Starting Date",
  endingDate: "Ending Date",
  lowerLimit: "Lower Limit",
  upperLimit: "Upper Limit",
  priority: "Priority",
  currency: "Currency",
  distributionChannel: "Distribution Channel",
  customer: "Customer No",
  customerGrp: "Customer Group",
  customerHierarchy: "Customer Hierarchy",
  locationCode: "Location Code",
  itemNo: "Item No",
  uom: "Unit of Measure",
  zoneCode: "Transportation Zone Code",
};

function nowForInput() {
  const date = new Date(Date.now() - new Date().getTimezoneOffset() * 60000);
  return date.toISOString().slice(0, 19).replace("T", " ");
}

function endOfTodayForInput() {
  const date = new Date();
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day} 23:59:59`;
}

function inputDate(value) {
  return value ? String(value).replace(" ", "T").slice(0, 19) : "";
}

function displayDate(value) {
  return value ? String(value).replace("T", " ") : "";
}

function newItem(mode) {
  return {
    id: `new-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
    active: true,
    conditionType: mode === "discount" ? "ZDIS" : "ZEN1",
    itemNo: "",
    customer: "",
    customerGrp: "",
    customerHierarchy: "",
    distributionChannel: "10",
    locationCode: "2112",
    priority: "1",
    currency: "AED",
    salesPrice: "",
    uom: "PAC",
    minQty: "1",
    startingDate: nowForInput(),
    endingDate: endOfTodayForInput(),
    lowerLimit: "",
    upperLimit: "",
    zoneCode: "",
    offerArticle: "No",
  };
}

export function ItemManagementView({
  mode,
  items = [],
  onItemsChange,
  onOpenCsv,
  onNotify,
}) {
  const [itemNoList, setItemNoList] = useState([""]);
  const [activeFilter, setActiveFilter] = useState("true");
  const [filterChips, setFilterChips] = useState([]);
  const [newRows, setNewRows] = useState([]);
  const [pendingUpdates, setPendingUpdates] = useState({});
  const [currentPage, setCurrentPage] = useState(1);
  const [totalRecords, setTotalRecords] = useState(0);
  const [serverLimit, setServerLimit] = useState(100);
  const [editingCell, setEditingCell] = useState(null);
  const [editingValue, setEditingValue] = useState("");
  const [columnWidths, setColumnWidths] = useState({});
  const [hasFetched, setHasFetched] = useState(false);
  const [fetchLoading, setFetchLoading] = useState(false);

  const resizingRef = useRef(null);
  const dragScrollRef = useRef(null);

  
  const storageKey = `jh_col_widths_${mode}`;

  // Load saved column widths.
  useEffect(() => {
    try {
      const saved = JSON.parse(localStorage.getItem(storageKey) || "{}");
      const initial = {};

      COLUMNS.forEach((column) => {
        initial[column.key] = saved[column.key] || column.width;
      });

      setColumnWidths(initial);
    } catch {
      const initial = {};

      COLUMNS.forEach((column) => {
        initial[column.key] = column.width;
      });

      setColumnWidths(initial);
    }
  }, [storageKey]);

  // Save column widths.
  useEffect(() => {
    if (!Object.keys(columnWidths).length) return;
    localStorage.setItem(storageKey, JSON.stringify(columnWidths));
  }, [columnWidths, storageKey]);

  // Column resizing.
  useEffect(() => {
    const move = (event) => {
      if (!resizingRef.current) return;

      const { key, startX, startWidth } = resizingRef.current;

      setColumnWidths((previous) => ({
        ...previous,
        [key]: Math.max(30, startWidth + event.clientX - startX),
      }));
    };

    const stop = () => {
      resizingRef.current = null;
      document.body.classList.remove("dm-col-resizing");
    };

    window.addEventListener("pointermove", move);
    window.addEventListener("pointerup", stop);

    return () => {
      window.removeEventListener("pointermove", move);
      window.removeEventListener("pointerup", stop);
    };
  }, []);

  // Excel-style click-and-drag scrolling.
  const startTableDrag = (event) => {
    if (event.button !== 0) return;

    if (
      event.target.closest(
        "input, select, textarea, button, a, .col-resizer, .editable-cell"
      )
    ) {
      return;
    }

    const container = event.currentTarget;

    dragScrollRef.current = {
      container,
      startX: event.clientX,
      startY: event.clientY,
      scrollLeft: container.scrollLeft,
      scrollTop: container.scrollTop,
      isDragging: false,
    };
  };

  useEffect(() => {
    const handleDragMove = (event) => {
      const drag = dragScrollRef.current;
      if (!drag) return;

      const deltaX = event.clientX - drag.startX;
      const deltaY = event.clientY - drag.startY;

      if (
        !drag.isDragging &&
        (Math.abs(deltaX) > 4 || Math.abs(deltaY) > 4)
      ) {
        drag.isDragging = true;
        document.body.classList.add("dm-table-dragging");
      }

      if (!drag.isDragging) return;

      event.preventDefault();

      drag.container.scrollLeft = drag.scrollLeft - deltaX;
      drag.container.scrollTop = drag.scrollTop - deltaY;
    };

    const stopTableDrag = () => {
      if (dragScrollRef.current?.isDragging) {
        document.body.classList.remove("dm-table-dragging");
      }

      dragScrollRef.current = null;
    };

    window.addEventListener("pointermove", handleDragMove);
    window.addEventListener("pointerup", stopTableDrag);
    window.addEventListener("pointercancel", stopTableDrag);

    return () => {
      window.removeEventListener("pointermove", handleDragMove);
      window.removeEventListener("pointerup", stopTableDrag);
      window.removeEventListener("pointercancel", stopTableDrag);
      document.body.classList.remove("dm-table-dragging");
    };
  }, []);

  const notify = (message, type = "success") => {
    onNotify?.(message, type);
  };

  const modeItems = useMemo(
    () =>
      items.filter((item) =>
        mode === "discount"
          ? item.conditionType === "ZDIS"
          : item.conditionType !== "ZDIS"
      ),
    [items, mode]
  );

  const filteredItems = useMemo(() => {
    let result = [...modeItems];

    const itemNumbers = itemNoList
      .map((value) => value.trim().toLowerCase())
      .filter(Boolean);

    if (hasFetched && itemNumbers.length) {
      result = result.filter((item) =>
        itemNumbers.some((number) =>
          String(item.itemNo || "").toLowerCase().includes(number)
        )
      );
    }

    if (hasFetched && activeFilter !== "") {
      result = result.filter(
        (item) => Boolean(item.active) === (activeFilter === "true")
      );
    }

    filterChips.forEach((chip) => {
      if (!chip.value) return;

      const field =
        chip.type === "customer_group_hierarchy"
          ? chip.subType
          : chip.type;

      if (chip.type === "sort_by") {
        result.sort((a, b) =>
          String(a[chip.value] || "").localeCompare(
            String(b[chip.value] || ""),
            undefined,
            { numeric: true }
          )
        );

        return;
      }

      result = result.filter((item) =>
        String(item[field] ?? "")
          .toLowerCase()
          .includes(String(chip.value).toLowerCase())
      );
    });

    return result;
  }, [modeItems, itemNoList, activeFilter, filterChips, hasFetched]);

  const totalPages = Math.max(
  1,
  Math.ceil(totalRecords / serverLimit)
);

// Backend already returns records for the requested page.
const visibleItems = filteredItems;

  
const handleFetch = async () => {
  try {
    setFetchLoading(true);

    console.log("Request Payload:", {
      page: currentPage,
    });

    const apiResponse = await fetchAllItemPrices(currentPage);

    console.log("Complete Backend Response:", apiResponse);

    const responseData = apiResponse?.response;

    const records = responseData?.data;
    const customFields = responseData?.custom_fields;

    if (!Array.isArray(records)) {
      throw new Error("Invalid item records in API response.");
    }

    const formattedItems = records.map((row) => fromDbRow(row));

    // Update the existing table.
    onItemsChange(formattedItems);

    // Update backend pagination information.
    setTotalRecords(
  Number(customFields?.total_records ?? records.length)
);

setServerLimit(Number(customFields?.limit || 100));

    setHasFetched(true);

    console.log("Formatted Items:", formattedItems);
    console.log("Backend Pagination:", customFields);

  } catch (error) {
    console.error("Fetch API Error:", error);

    notify(
      error.message || "Unable to fetch item prices.",
      "error"
    );

  } finally {
    setFetchLoading(false);
  }
};
// useEffect(() => {
//   handleFetch();
//   // eslint-disable-next-line react-hooks/exhaustive-deps
// }, []);
useEffect(() => {
  handleFetch();

  // eslint-disable-next-line react-hooks/exhaustive-deps
}, [currentPage, mode]);



  const addItemNo = () =>
    setItemNoList((previous) => [...previous, ""]);

  const changeItemNo = (index, value) => {
    setItemNoList((previous) =>
      previous.map((item, itemIndex) =>
        itemIndex === index ? value : item
      )
    );
  };

  const removeItemNo = (index) => {
    setItemNoList((previous) =>
      previous.length === 1
        ? previous
        : previous.filter((_, itemIndex) => itemIndex !== index)
    );
  };

  const addFilter = (type) => {
    if (
      !type ||
      filterChips.some((chip) => chip.id === `filter-${type}`)
    ) {
      return;
    }

    setFilterChips((previous) => [
      ...previous,
      {
        id: `filter-${type}`,
        type,
        subType: "customer",
        value: "",
      },
    ]);
  };

  const changeFilter = (id, value, subType) => {
    setFilterChips((previous) =>
      previous.map((chip) =>
        chip.id === id
          ? {
            ...chip,
            value,
            ...(subType ? { subType } : {}),
          }
          : chip
      )
    );
  };

  const removeFilter = (id) => {
    setFilterChips((previous) =>
      previous.filter((chip) => chip.id !== id)
    );
  };

  const addNewRow = () => {
    setNewRows((previous) => [newItem(mode), ...previous]);
  };

  const changeNewRow = (id, field, value) => {
    setNewRows((previous) =>
      previous.map((row) =>
        row.id === id ? { ...row, [field]: value } : row
      )
    );
  };

  const toggleActive = (id, isNew) => {
    if (isNew) {
      setNewRows((previous) =>
        previous.map((row) =>
          row.id === id ? { ...row, active: !row.active } : row
        )
      );

      return;
    }

    const item = modeItems.find((row) => row.id === id);
    if (!item) return;

    const current = pendingUpdates[id] || {};
    const active = !(current.active ?? item.active);

    setPendingUpdates((previous) => ({
      ...previous,
      [id]: {
        ...previous[id],
        active,
        ...(!active ? { endingDate: nowForInput() } : {}),
      },
    }));
  };

  // Select or deselect all items in the current mode.
  const toggleAllActive = (checked) => {
    // Update newly added rows.
    setNewRows((previous) =>
      previous.map((row) => ({
        ...row,
        active: checked,
        ...(!checked ? { endingDate: nowForInput() } : {}),
      }))
    );

    // Update existing rows.
    const updates = {};

    modeItems.forEach((item) => {
      updates[item.id] = {
        ...pendingUpdates[item.id],
        active: checked,
        ...(!checked ? { endingDate: nowForInput() } : {}),
      };
    });

    setPendingUpdates((previous) => ({
      ...previous,
      ...updates,
    }));
  };

  const updatePending = (id, field, value) => {
    setPendingUpdates((previous) => ({
      ...previous,
      [id]: {
        ...previous[id],
        [field]: value,
      },
    }));
  };

  const validate = (row, isNew) => {
    const errors = [];
    const priority = Number(row.priority);

    ["salesPrice", "lowerLimit", "upperLimit", "minQty"].forEach(
      (field) => {
        if (
          row[field] !== "" &&
          row[field] != null &&
          !Number.isFinite(Number(row[field]))
        ) {
          errors.push(`${LABELS[field] || field} must be a number`);
        }
      }
    );

    const sales = Number(row.salesPrice);
    const lower = Number(row.lowerLimit);
    const upper = Number(row.upperLimit);

    if (row.salesPrice !== "" && sales <= 0) {
      errors.push("Sales Price must be greater than 0");
    }

    if (row.lowerLimit !== "" && lower <= 0) {
      errors.push("Lower Limit must be greater than 0");
    }

    if (row.upperLimit !== "" && upper <= 0) {
      errors.push("Upper Limit must be greater than 0");
    }

    if (
      row.lowerLimit !== "" &&
      row.upperLimit !== "" &&
      lower > upper
    ) {
      errors.push("Lower Limit cannot be greater than Upper Limit");
    }

    if (
      row.salesPrice !== "" &&
      row.lowerLimit !== "" &&
      sales < lower
    ) {
      errors.push("Sales Price cannot be less than Lower Limit");
    }

    if (
      row.salesPrice !== "" &&
      row.upperLimit !== "" &&
      sales > upper
    ) {
      errors.push("Sales Price cannot be greater than Upper Limit");
    }

    if (
      row.startingDate &&
      row.endingDate &&
      row.startingDate > row.endingDate
    ) {
      errors.push("Starting Date cannot be after Ending Date");
    }

    if (isNew) {
      [
        "conditionType",
        "salesPrice",
        "startingDate",
        "endingDate",
        "lowerLimit",
        "upperLimit",
        "currency",
      ].forEach((field) => {
        if (String(row[field] ?? "").trim() === "") {
          errors.push(`${LABELS[field] || field} is required`);
        }
      });

      if (
        !Number.isInteger(priority) ||
        priority < 1 ||
        priority > 11
      ) {
        errors.push("Priority must be between 1 and 11");
      } else {
        PRIORITY_CONFIG[priority - 1].forEach((field) => {
          if (String(row[field] ?? "").trim() === "") {
            errors.push(
              `${LABELS[field] || field} is required for priority ${priority}`
            );
          }
        });
      }
    }

    return errors;
  };

  const deleteExisting = (item) => {
    const confirmed = window.confirm(
      `Delete item condition for item "${item.itemNo || item.id}"?`
    );

    if (!confirmed) return;

    onItemsChange((previous) =>
      previous.filter((row) => row.id !== item.id)
    );

    setPendingUpdates((previous) => {
      const next = { ...previous };
      delete next[item.id];
      return next;
    });

    notify("Item condition deleted from demo data.");
  };

  // const saveChanges = () => {
  //   const newItems = newRows.filter((row) => row.itemNo.trim());

  //   for (const row of newItems) {
  //     const errors = validate(row, true);

  //     if (errors.length) {
  //       notify(
  //         `Item ${row.itemNo || "(unspecified)"}:\n${errors.join("\n")}`,
  //         "error"
  //       );

  //       return;
  //     }
  //   }

  //   const updates = Object.entries(pendingUpdates);

  //   if (!newItems.length && !updates.length) {
  //     notify("No changes to save.", "info");
  //     return;
  //   }

  //   const savedNewItems = newItems.map((row) => ({
  //     ...row,
  //     salesPrice: Number(row.salesPrice),
  //     lowerLimit: Number(row.lowerLimit),
  //     upperLimit: Number(row.upperLimit),
  //     minQty: Number(row.minQty),
  //     status: "Success",
  //   }));

  //   // Display sample JSON payload
  //   // console.log(
  //   //   "Sample Payload:",
  //   //   JSON.stringify(savedNewItems, null, 2)
  //   // );

  //   onItemsChange((previous) => {
  //     const updated = previous.map((item) => {
  //       const changes = pendingUpdates[item.id];

  //       return changes
  //         ? { ...item, ...changes, status: "Success" }
  //         : item;
  //     });

  //     return [...savedNewItems, ...updated];
  //   });

  //   setNewRows([]);
  //   setPendingUpdates({});

  //   notify(
  //     `${savedNewItems.length} item(s) created and ${updates.length} item(s) updated in demo mode.`
  //   );
  // };

  const saveChanges = async () => {
  const newItems = newRows.filter((row) => row.itemNo.trim());

  // Validate new records
  for (const row of newItems) {
    const errors = validate(row, true);

    if (errors.length) {
      notify(
        `Item ${row.itemNo || "(unspecified)"}:\n${errors.join("\n")}`,
        "error"
      );
      return;
    }
  }

  const updates = Object.entries(pendingUpdates);

  if (!newItems.length && !updates.length) {
    notify("No changes to save.", "info");
    return;
  }

  // Existing item updates are not connected to an API yet.
  if (!newItems.length && updates.length) {
    notify(
      "Creating new records is supported, but updating existing records requires an update API.",
      "info"
    );
    return;
  }

  try {
    const conditionType =
      mode === "discount" ? "ZDIS" : "ZEN1";

    const result = await createSingleItemPrice(
      newItems,
      conditionType
    );

    const createdRecords = result.data?.created_records || [];
    const createdCount = result.data?.created_count || 0;
    const failedCount = result.data?.failed_count || 0;

    // Match successfully created records with frontend rows.
    const successfulItems = newItems.filter((item) =>
      createdRecords.some(
        (record) =>
          record.item_no === item.itemNo &&
          record.condition_type === conditionType
      )
    );

    const savedItems = successfulItems.map((item) => {
      const record = createdRecords.find(
        (record) =>
          record.item_no === item.itemNo &&
          record.condition_type === conditionType
      );

      return {
        ...item,
        id: record?.id ?? item.id,
        salesPrice: Number(item.salesPrice),
        lowerLimit: Number(item.lowerLimit),
        upperLimit: Number(item.upperLimit),
        minQty: Number(item.minQty),
        status: "Success",
      };
    });

    onItemsChange((previous) => [
      ...savedItems,
      ...previous,
    ]);

    // Keep unsuccessful records so they can be corrected and retried.
    const failedItems = newItems.filter(
      (item) => !successfulItems.includes(item)
    );

    setNewRows(failedItems);

    if (createdCount > 0) {
      notify(
        `${createdCount} item(s) created successfully. ${
          failedCount > 0
            ? `${failedCount} item(s) failed.`
            : ""
        }`,
        failedCount > 0 ? "error" : "success"
      );
    } else {
      notify(
        result.message || "No records were created.",
        "error"
      );
    }

    // Existing edits remain pending because no update API is connected.
  } catch (error) {
    console.error("Save Items Error:", error);
    notify(error.message || "Failed to create records.", "error");
  }
};

  // FIXED: Export rows as objects and use the correct rowsToCsv arguments.
  const downloadCsv = () => {
    try {
      const headers = COLUMNS.map((column) => column.label);

      const rows = filteredItems.map((item) => {
        const pending = pendingUpdates[item.id] || {};

        return COLUMNS.reduce((row, column) => {
          row[column.label] =
            column.type === "active"
              ? (pending.active ?? item.active)
                ? "TRUE"
                : "FALSE"
              : pending[column.key] ?? item[column.key] ?? "";

          return row;
        }, {});
      });

      const csv = rowsToCsv(rows, headers);

      saveCsvFile(csv, `${mode}_management.csv`);
    } catch (error) {
      console.error("CSV download error:", error);
      notify("CSV download failed.", "error");
    }
  };

  const startResize = (key, event) => {
    event.preventDefault();
    event.stopPropagation();

    resizingRef.current = {
      key,
      startX: event.clientX,
      startWidth:
        columnWidths[key] ||
        COLUMNS.find((column) => column.key === key).width,
    };

    document.body.classList.add("dm-col-resizing");
  };

  const resetWidths = () => {
    const reset = {};

    COLUMNS.forEach((column) => {
      reset[column.key] = column.width;
    });

    setColumnWidths(reset);
  };

  const renderNewCell = (row, column) => {
    const value = row[column.key] ?? "";

    if (column.type === "select") {
      return (
        <select
          value={value}
          onChange={(event) =>
            changeNewRow(row.id, column.key, event.target.value)
          }
        >
          <option value=""></option>

          {column.options.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
      );
    }

    if (column.type === "datetime") {
      return (
        <input
          type="datetime-local"
          step="1"
          value={inputDate(value)}
          onChange={(event) =>
            changeNewRow(
              row.id,
              column.key,
              displayDate(event.target.value)
            )
          }
        />
      );
    }

    return (
      <input
        type={column.type === "number" ? "number" : "text"}
        step={column.type === "number" ? "any" : undefined}
        placeholder={column.label}
        value={value}
        onChange={(event) =>
          changeNewRow(row.id, column.key, event.target.value)
        }
        autoComplete="off"
      />
    );
  };

  const renderExistingCell = (item, column) => {
    const pending = pendingUpdates[item.id] || {};
    const value = pending[column.key] ?? item[column.key] ?? "";

    const isEditing =
      editingCell?.id === item.id &&
      editingCell?.field === column.key;

    if (column.type === "active") {
      return (
        <button
          type="button"
          className={`active-tick-btn ${(pending.active ?? item.active) ? "" : "inactive"
            }`}
          title="Toggle active"
          onClick={() => toggleActive(item.id, false)}
        >
          {(pending.active ?? item.active) ? "✓" : ""}
        </button>
      );
    }

    if (!column.editable) return value;

    if (isEditing) {
      if (column.type === "select") {
        return (
          <select
            autoFocus
            value={editingValue}
            onChange={(event) =>
              setEditingValue(event.target.value)
            }
            onBlur={() => {
              updatePending(item.id, column.key, editingValue);
              setEditingCell(null);
            }}
          >
            {column.options.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        );
      }

      return (
        <input
          autoFocus
          type={
            column.type === "datetime"
              ? "datetime-local"
              : column.type === "number"
                ? "number"
                : "text"
          }
          step={
            column.type === "number" || column.type === "datetime"
              ? "any"
              : undefined
          }
          value={
            column.type === "datetime"
              ? inputDate(editingValue)
              : editingValue
          }
          onChange={(event) =>
            setEditingValue(
              column.type === "datetime"
                ? displayDate(event.target.value)
                : event.target.value
            )
          }
          onBlur={() => {
            updatePending(item.id, column.key, editingValue);
            setEditingCell(null);
          }}
          onKeyDown={(event) => {
            if (event.key === "Enter") {
              updatePending(item.id, column.key, editingValue);
              setEditingCell(null);
            }

            if (event.key === "Escape") {
              setEditingCell(null);
            }
          }}
        />
      );
    }

    return (
      <span
        className="editable-cell"
        title="Click to edit"
        onClick={() => {
          setEditingCell({ id: item.id, field: column.key });
          setEditingValue(String(value));
        }}
      >
        {value}
      </span>
    );
  };

  const hasNewRows = newRows.length > 0;

  // Check whether all items in the current mode are active.
  const allActive =
    [...modeItems, ...newRows].length > 0 &&
    [...modeItems, ...newRows].every((item) => {
      const pending = pendingUpdates[item.id] || {};
      return pending.active ?? item.active;
    });

  const saveDisabled =
    !newRows.some((row) => row.itemNo.trim()) &&
    Object.keys(pendingUpdates).length === 0;

  // Calculate proportional widths from the user's saved column widths.
  const totalColumnWidth = COLUMNS.reduce(
    (total, column) =>
      total + (columnWidths[column.key] || column.width),
    0
  );

  // Reserve a small amount of space for the Action column when adding rows.
  const actionColumnWidth = hasNewRows ? 4 : 0;
  const dataColumnWidth = 100 - actionColumnWidth;

  return (
    <div className="item-management-container">
      <div className="toolbar-form">
        <div className="filters-row">
          
          <div id="itemNoContainer">
            <div className="item-no-row">
              <input
                type="text"
                className="itemNoInput"
                placeholder="Item No"
                value={itemNoList[0]}
                onChange={(event) =>
                  changeItemNo(0, event.target.value)
                }
                autoComplete="off"
              />
            </div>
          </div>

          <div className="core-field">
            <select
              id="fetchActive"
              className="form-control"
              value={activeFilter}
              onChange={(event) =>
                setActiveFilter(event.target.value)
              }
            >
              <option value="true">Active</option>
              <option value="false">Inactive</option>
              <option value="">All</option>
            </select>
          </div>

          <div className="core-field filter-field">
            <select
              id="addFilterSelect"
              className="form-control"
              value=""
              onChange={(event) => addFilter(event.target.value)}
            >
              <option value="">+ Add filter</option>

              {FILTER_OPTIONS.map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </div>

          <div className="toolbar-actions">
            <button
              type="button"
              id="fetch"
              className="btn btn-primary"
              onClick={handleFetch}
              disabled={fetchLoading}
            >
              <FaSearch />
              {fetchLoading ? "Fetching..." : "Fetch"}
            </button>

            <button
              type="button"
              id="downloadCsvBtn"
              className="btn btn-outline"
              onClick={downloadCsv}
            >
              <i className="fas fa-download"></i>
              <FaDownload />
              CSV
            </button>

            <button
              type="button"
              id="importBtnUnique"
              className="btn btn-outline"
              onClick={() => onOpenCsv(mode)}
            >
              <i className="fas fa-file-import"></i>
              <FaFileImport />
              Import
            </button>

            <button
              type="button"
              id="addItemBtn"
              className="btn btn-success"
              onClick={addNewRow}
            >
              <i className="fas fa-plus"></i>
              <FaPlus />
              Add Item
            </button>

            <button
              type="button"
              id="saveUpdateBtn"
              className="btn"
              disabled={saveDisabled}
              onClick={saveChanges}
            >
              Save
            </button>
          </div>
        </div>

        {filterChips.length > 0 && (
          <div id="activeFilters" className="active-filters">
            {filterChips.map((chip) => {
              if (chip.type === "customer_group_hierarchy") {
                return (
                  <div
                    key={chip.id}
                    className="filter-chip customer-hierarchy-filter"
                  >
                    <label className="customer-filter-label">
                      CUSTOMER
                    </label>

                    <select
                      className="customer-filter-type"
                      value={chip.subType}
                      onChange={(event) =>
                        changeFilter(
                          chip.id,
                          chip.value,
                          event.target.value
                        )
                      }
                    >
                      <option value="customer">Customer No</option>
                      <option value="customerGrp">Customer Group</option>
                      <option value="customerHierarchy">
                        Customer Hierarchy
                      </option>
                    </select>

                    <input
                      className="customer-filter-value"
                      placeholder="Value"
                      value={chip.value}
                      onChange={(event) =>
                        changeFilter(chip.id, event.target.value)
                      }
                    />

                    <button
                      type="button"
                      className="customer-filter-remove"
                      onClick={() => removeFilter(chip.id)}
                    >
                      ×
                    </button>
                  </div>
                );
              }

              if (chip.type === "sort_by") {
                return (
                  <div key={chip.id} className="filter-chip">
                    <label>Sort By</label>

                    <select
                      value={chip.value}
                      onChange={(event) =>
                        changeFilter(chip.id, event.target.value)
                      }
                    >
                      <option value="">-- Select --</option>
                      <option value="startingDate">Starting Date</option>
                      <option value="endingDate">Ending Date</option>
                      <option value="itemNo">Item No</option>
                      <option value="salesPrice">Sales Price</option>
                    </select>

                    <button
                      type="button"
                      className="remove-filter"
                      onClick={() => removeFilter(chip.id)}
                    >
                      ×
                    </button>
                  </div>
                );
              }

              const label =
                FILTER_OPTIONS.find(
                  ([value]) => value === chip.type
                )?.[1] || chip.type;

              const isDate = [
                "startingDate",
                "endingDate",
              ].includes(chip.type);

              const isNumber = [
                "salesPrice",
                "minQty",
                "lowerLimit",
                "upperLimit",
                "priority",
              ].includes(chip.type);

              return (
                <div key={chip.id} className="filter-chip">
                  <label>{label}</label>

                  <input
                    type={
                      isDate
                        ? "datetime-local"
                        : isNumber
                          ? "number"
                          : "text"
                    }
                    placeholder={label}
                    value={chip.value}
                    onChange={(event) =>
                      changeFilter(chip.id, event.target.value)
                    }
                  />

                  <button
                    type="button"
                    className="remove-filter"
                    onClick={() => removeFilter(chip.id)}
                  >
                    ×
                  </button>
                </div>
              );
            })}
          </div>
        )}
      </div>

      <div className="results-section">
        <div
          className="table-responsive"
          onPointerDown={startTableDrag}
        >
          <table
            className={`table ${hasNewRows ? "has-new-rows" : ""
              }`}
            style={{
              width: "100%",
              minWidth: 0,
              maxWidth: "100%",
              tableLayout: "fixed",
            }}
          >
            {/* Column widths are proportional, so all columns fit. */}
            <colgroup>
              {COLUMNS.map((column) => {
                const savedWidth =
                  columnWidths[column.key] || column.width;

                const percentage =
                  (savedWidth / totalColumnWidth) *
                  dataColumnWidth;

                return (
                  <col
                    key={column.key}
                    style={{
                      width: `${percentage}%`,
                    }}
                  />
                );
              })}

              {hasNewRows && (
                <col
                  style={{
                    width: `${actionColumnWidth}%`,
                  }}
                />
              )}
            </colgroup>

            <thead>
              <tr id="itemPriceTableHead">
                {COLUMNS.map((column) => (
                  <th
                    key={column.key}
                    style={{
                      position: "relative",
                    }}
                  >
                    {column.key === "active" ? (
                      <div
                        style={{
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                          gap: "4px",
                        }}
                      >
                        <input
                          type="checkbox"
                          checked={allActive}
                          onChange={(event) =>
                            toggleAllActive(event.target.checked)
                          }
                          title="Select All Active"
                        />

                        <span>Active</span>
                      </div>
                    ) : (
                      column.label
                    )}

                    <div
                      className="col-resizer"
                      title="Drag to resize · double-click to reset all"
                      onPointerDown={(event) =>
                        startResize(column.key, event)
                      }
                      onDoubleClick={resetWidths}
                    />
                  </th>
                ))}

                {hasNewRows && (
                  <th className="fixed-action-column action-col">
                    Action
                  </th>
                )}
              </tr>
            </thead>

            <tbody id="itemPriceTableBody">
              {newRows.map((row) => (
                <tr key={row.id} className="new-item-row">
                  <td>
                    <button
                      type="button"
                      className={`active-tick-btn ${row.active ? "" : "inactive"
                        }`}
                      title="Toggle active"
                      onClick={() => toggleActive(row.id, true)}
                    >
                      {row.active ? "✓" : ""}
                    </button>
                  </td>

                  {COLUMNS.slice(1).map((column) => (
                    <td key={column.key}>
                      {renderNewCell(row, column)}
                    </td>
                  ))}

                  <td className="action-cell">
                    <button
                      type="button"
                      className="delete-row-btn"
                      title="Remove row"
                      onClick={() =>
                        setNewRows((previous) =>
                          previous.filter(
                            (item) => item.id !== row.id
                          )
                        )
                      }
                    >
                      ×
                    </button>
                  </td>
                </tr>
              ))}

              {visibleItems.length === 0 && newRows.length === 0 ? (
                <tr>
                  <td
                    colSpan={COLUMNS.length + (hasNewRows ? 1 : 0)}
                    className="no-items-cell"
                  >
                    No items found
                  </td>
                </tr>
              ) : (
                visibleItems.map((item) => {
                  const dirty = Boolean(pendingUpdates[item.id]);

                  return (
                    <tr
                      key={item.id}
                      className={dirty ? "dirty-row" : ""}
                    >
                      {COLUMNS.map((column) => (
                        <td key={column.key}>
                          {renderExistingCell(item, column)}
                        </td>
                      ))}
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      <div className="pagination-container">
        <button
          type="button"
          disabled={currentPage <= 1}
          onClick={() =>
            setCurrentPage((page) => Math.max(1, page - 1))
          }
        >
          Previous
        </button>

       <span>
  Page {currentPage} / {totalPages} &nbsp;·&nbsp;{" "}
  {totalRecords} rows
</span>

        <button
          type="button"
          disabled={currentPage >= totalPages}
          onClick={() =>
            setCurrentPage((page) =>
              Math.min(totalPages, page + 1)
            )
          }
        >
          Next
        </button>
      </div>
    </div>
  );
}














// import { useEffect, useMemo, useRef, useState } from "react";
// import {
//   downloadCsv as saveCsvFile,
//   rowsToCsv,
//   fetchAllItemPrices,
//   fromDbRow,
// } from "../api";


// import {
//   FaSearch,
//   FaDownload,
//   FaFileImport,
//   FaPlus,
// } from "react-icons/fa";

// // const UOM_OPTIONS = ["PAC", "EA", "CAR"];
// const LOCATION_OPTIONS = ["2112", "2113", "2132"];
// // const CURRENCY_OPTIONS = ["AED", "USD", "EUR", "GBP", "JPY", "CAD", "AUD"];
// const PRIORITY_OPTIONS = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11"];

// const COLUMNS = [
//   { key: "active", label: "Active", type: "active", width: 45 },
//   { key: "conditionType", label: "Condition Type", type: "text", width: 95 },
//   { key: "itemNo", label: "Item No", type: "text", width: 80 },
//   { key: "customer", label: "Customer", type: "text", width: 85 },
//   { key: "customerGrp", label: "Customer Grp", type: "text", width: 85 },
//   { key: "customerHierarchy", label: "Customer Hierarchy", type: "text", width: 95 },
//   { key: "distributionChannel", label: "Distribution Channel", type: "text", width: 105 },
//   { key: "locationCode", label: "Location Code", type: "select", options: LOCATION_OPTIONS, width: 90, editable: true },
//   { key: "priority", label: "Priority", type: "select", options: PRIORITY_OPTIONS, width: 65, editable: true },
//   // { key: "currency", label: "Currency", type: "select", options: CURRENCY_OPTIONS, width: 70, editable: true },
//   { key: "currency", label: "Currency", type: "text", width: 70, editable: true },
//   { key: "salesPrice", label: "Sales Price", type: "number", width: 80, editable: true },
//   // { key: "uom", label: "UOM", type: "select", options: UOM_OPTIONS, width: 60, editable: true },
//   { key: "uom", label: "UOM", type: "text", width: 60, editable: true },
//   { key: "minQty", label: "Min Qty", type: "number", width: 65, editable: true },
//   { key: "startingDate", label: "Starting Date", type: "datetime", width: 145, editable: true },
//   { key: "endingDate", label: "Ending Date", type: "datetime", width: 145, editable: true },
//   { key: "lowerLimit", label: "Lower Limit", type: "number", width: 80, editable: true },
//   { key: "upperLimit", label: "Upper Limit", type: "number", width: 80, editable: true },
//   { key: "zoneCode", label: "Zone Code", type: "text", width: 85, editable: true },
//   { key: "offerArticle", label: "Offer Article", type: "text", width: 85, editable: true },
// ];

// const FILTER_OPTIONS = [
//   ["customer_group_hierarchy", "Customer / Group / Hierarchy"],
//   ["sort_by", "Sort By"],
//   ["salesOrganization", "Sales Organization"],
//   ["distributionChannel", "Distribution Channel"],
//   ["locationCode", "Location Code"],
//   ["conditionType", "Condition Type"],
//   ["salesPrice", "Sales Price"],
//   ["currency", "Currency"],
//   ["uom", "Unit of Measure"],
//   ["minQty", "Minimum Quantity"],
//   ["lowerLimit", "Lower Limit"],
//   ["upperLimit", "Upper Limit"],
//   ["zoneCode", "Transportation Zone"],
//   ["startingDate", "Starting Date"],
//   ["endingDate", "Ending Date"],
//   ["priority", "Priority"],
//   ["offerArticle", "Offer Article"],
// ];

// const PRIORITY_CONFIG = [
//   ["distributionChannel", "customer", "locationCode", "itemNo", "uom"],
//   ["distributionChannel", "customerGrp", "locationCode", "itemNo", "uom"],
//   ["distributionChannel", "customer", "itemNo", "uom"],
//   ["distributionChannel", "customerGrp", "itemNo", "uom"],
//   ["customerGrp", "itemNo", "uom"],
//   ["customerHierarchy", "locationCode", "itemNo", "uom"],
//   ["customerHierarchy", "itemNo", "uom"],
//   ["distributionChannel", "locationCode", "itemNo", "zoneCode", "uom"],
//   ["distributionChannel", "locationCode", "itemNo", "uom"],
//   ["distributionChannel", "itemNo", "uom"],
//   ["itemNo", "uom"],
// ];

// const LABELS = {
//   conditionType: "Condition Type",
//   salesPrice: "Sales Price",
//   startingDate: "Starting Date",
//   endingDate: "Ending Date",
//   lowerLimit: "Lower Limit",
//   upperLimit: "Upper Limit",
//   priority: "Priority",
//   currency: "Currency",
//   distributionChannel: "Distribution Channel",
//   customer: "Customer No",
//   customerGrp: "Customer Group",
//   customerHierarchy: "Customer Hierarchy",
//   locationCode: "Location Code",
//   itemNo: "Item No",
//   uom: "Unit of Measure",
//   zoneCode: "Transportation Zone Code",
// };

// function nowForInput() {
//   const date = new Date(Date.now() - new Date().getTimezoneOffset() * 60000);
//   return date.toISOString().slice(0, 19).replace("T", " ");
// }

// function endOfTodayForInput() {
//   const date = new Date();
//   const year = date.getFullYear();
//   const month = String(date.getMonth() + 1).padStart(2, "0");
//   const day = String(date.getDate()).padStart(2, "0");
//   return `${year}-${month}-${day} 23:59:59`;
// }

// function inputDate(value) {
//   return value ? String(value).replace(" ", "T").slice(0, 19) : "";
// }

// function displayDate(value) {
//   return value ? String(value).replace("T", " ") : "";
// }

// function newItem(mode) {
//   return {
//     id: `new-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
//     active: true,
//     conditionType: mode === "discount" ? "ZDIS" : "ZEN1",
//     itemNo: "",
//     customer: "",
//     customerGrp: "",
//     customerHierarchy: "",
//     distributionChannel: "10",
//     locationCode: "2112",
//     priority: "1",
//     currency: "AED",
//     salesPrice: "",
//     uom: "PAC",
//     minQty: "1",
//     startingDate: nowForInput(),
//     endingDate: endOfTodayForInput(),
//     lowerLimit: "",
//     upperLimit: "",
//     zoneCode: "",
//     offerArticle: "No",
//   };
// }

// export function ItemManagementView({
//   mode,
//   items = [],
//   onItemsChange,
//   onOpenCsv,
//   onNotify,
// }) {
//   const [itemNoList, setItemNoList] = useState([""]);
//   const [activeFilter, setActiveFilter] = useState("true");
//   const [filterChips, setFilterChips] = useState([]);
//   const [newRows, setNewRows] = useState([]);
//   const [pendingUpdates, setPendingUpdates] = useState({});
//   const [currentPage, setCurrentPage] = useState(1);
//   const [editingCell, setEditingCell] = useState(null);
//   const [editingValue, setEditingValue] = useState("");
//   const [columnWidths, setColumnWidths] = useState({});
//   const [hasFetched, setHasFetched] = useState(false);
//   const [fetchLoading, setFetchLoading] = useState(false);

//   const resizingRef = useRef(null);
//   const dragScrollRef = useRef(null);

//   const pageSize = 500;
//   const storageKey = `jh_col_widths_${mode}`;

//   // Load saved column widths.
//   useEffect(() => {
//     try {
//       const saved = JSON.parse(localStorage.getItem(storageKey) || "{}");
//       const initial = {};

//       COLUMNS.forEach((column) => {
//         initial[column.key] = saved[column.key] || column.width;
//       });

//       setColumnWidths(initial);
//     } catch {
//       const initial = {};

//       COLUMNS.forEach((column) => {
//         initial[column.key] = column.width;
//       });

//       setColumnWidths(initial);
//     }
//   }, [storageKey]);

//   // Save column widths.
//   useEffect(() => {
//     if (!Object.keys(columnWidths).length) return;
//     localStorage.setItem(storageKey, JSON.stringify(columnWidths));
//   }, [columnWidths, storageKey]);

//   // Column resizing.
//   useEffect(() => {
//     const move = (event) => {
//       if (!resizingRef.current) return;

//       const { key, startX, startWidth } = resizingRef.current;

//       setColumnWidths((previous) => ({
//         ...previous,
//         [key]: Math.max(30, startWidth + event.clientX - startX),
//       }));
//     };

//     const stop = () => {
//       resizingRef.current = null;
//       document.body.classList.remove("dm-col-resizing");
//     };

//     window.addEventListener("pointermove", move);
//     window.addEventListener("pointerup", stop);

//     return () => {
//       window.removeEventListener("pointermove", move);
//       window.removeEventListener("pointerup", stop);
//     };
//   }, []);

//   // Excel-style click-and-drag scrolling.
//   const startTableDrag = (event) => {
//     if (event.button !== 0) return;

//     if (
//       event.target.closest(
//         "input, select, textarea, button, a, .col-resizer, .editable-cell"
//       )
//     ) {
//       return;
//     }

//     const container = event.currentTarget;

//     dragScrollRef.current = {
//       container,
//       startX: event.clientX,
//       startY: event.clientY,
//       scrollLeft: container.scrollLeft,
//       scrollTop: container.scrollTop,
//       isDragging: false,
//     };
//   };

//   useEffect(() => {
//     const handleDragMove = (event) => {
//       const drag = dragScrollRef.current;
//       if (!drag) return;

//       const deltaX = event.clientX - drag.startX;
//       const deltaY = event.clientY - drag.startY;

//       if (
//         !drag.isDragging &&
//         (Math.abs(deltaX) > 4 || Math.abs(deltaY) > 4)
//       ) {
//         drag.isDragging = true;
//         document.body.classList.add("dm-table-dragging");
//       }

//       if (!drag.isDragging) return;

//       event.preventDefault();

//       drag.container.scrollLeft = drag.scrollLeft - deltaX;
//       drag.container.scrollTop = drag.scrollTop - deltaY;
//     };

//     const stopTableDrag = () => {
//       if (dragScrollRef.current?.isDragging) {
//         document.body.classList.remove("dm-table-dragging");
//       }

//       dragScrollRef.current = null;
//     };

//     window.addEventListener("pointermove", handleDragMove);
//     window.addEventListener("pointerup", stopTableDrag);
//     window.addEventListener("pointercancel", stopTableDrag);

//     return () => {
//       window.removeEventListener("pointermove", handleDragMove);
//       window.removeEventListener("pointerup", stopTableDrag);
//       window.removeEventListener("pointercancel", stopTableDrag);
//       document.body.classList.remove("dm-table-dragging");
//     };
//   }, []);

//   const notify = (message, type = "success") => {
//     onNotify?.(message, type);
//   };

//   const modeItems = useMemo(
//     () =>
//       items.filter((item) =>
//         mode === "discount"
//           ? item.conditionType === "ZDIS"
//           : item.conditionType !== "ZDIS"
//       ),
//     [items, mode]
//   );

//   const filteredItems = useMemo(() => {
//     let result = [...modeItems];

//     const itemNumbers = itemNoList
//       .map((value) => value.trim().toLowerCase())
//       .filter(Boolean);

//     if (hasFetched && itemNumbers.length) {
//       result = result.filter((item) =>
//         itemNumbers.some((number) =>
//           String(item.itemNo || "").toLowerCase().includes(number)
//         )
//       );
//     }

//     if (hasFetched && activeFilter !== "") {
//       result = result.filter(
//         (item) => Boolean(item.active) === (activeFilter === "true")
//       );
//     }

//     filterChips.forEach((chip) => {
//       if (!chip.value) return;

//       const field =
//         chip.type === "customer_group_hierarchy"
//           ? chip.subType
//           : chip.type;

//       if (chip.type === "sort_by") {
//         result.sort((a, b) =>
//           String(a[chip.value] || "").localeCompare(
//             String(b[chip.value] || ""),
//             undefined,
//             { numeric: true }
//           )
//         );

//         return;
//       }

//       result = result.filter((item) =>
//         String(item[field] ?? "")
//           .toLowerCase()
//           .includes(String(chip.value).toLowerCase())
//       );
//     });

//     return result;
//   }, [modeItems, itemNoList, activeFilter, filterChips, hasFetched]);

//   const totalPages = Math.max(
//     1,
//     Math.ceil(filteredItems.length / pageSize)
//   );

//   const visibleItems = filteredItems.slice(
//     (currentPage - 1) * pageSize,
//     currentPage * pageSize
//   );

//   // const handleFetch = async () => {
//   //   try {
//   //     setFetchLoading(true);

//   //     const response = await fetchAllItemPrices();

//   //     console.log("Backend Item Prices:", response);

//   //     // Identify the records returned by the backend.
//   //     const records = Array.isArray(response)
//   //       ? response
//   //       : Array.isArray(response.data)
//   //         ? response.data
//   //         : Array.isArray(response.items)
//   //           ? response.items
//   //           : Array.isArray(response.result)
//   //             ? response.result
//   //             : Array.isArray(response.data?.items)
//   //               ? response.data.items
//   //               : null;

//   //     if (!records) {
//   //       throw new Error(
//   //         "Unexpected API response. Please check the response structure."
//   //       );
//   //     }

      

//   //     const formattedItems = records.map(fromDbRow);

//   //     onItemsChange(formattedItems);

//   //     setHasFetched(true);
//   //     setCurrentPage(1);

//   //     notify(
//   //       `${formattedItems.length} item records fetched successfully.`,
//   //       "success"
//   //     );

//   //   } catch (error) {
//   //     console.error("Fetch API Error:", error);

//   //     notify(
//   //       error.message || "Unable to fetch item prices.",
//   //       "error"
//   //     );

//   //   } finally {
//   //     setFetchLoading(false);
//   //   }
//   // };






// //   const handleFetch = async () => {
// //   try {
// //     setFetchLoading(true);

// //     const response = await fetchAllItemPrices();

    
// //     console.log(response);
    

// //   } catch (error) {
// //     console.error("API Error:", error);
// //   } finally {
// //     setFetchLoading(false);
// //   }
// // };
// //   // Automatically fetch item prices when the page loads
// //   useEffect(() => {
// //     handleFetch();
// //     // eslint-disable-next-line react-hooks/exhaustive-deps
// //   }, []);








// // const handleFetch = async () => {
// //   try {
// //     setFetchLoading(true);

// //     const response = await fetchAllItemPrices();

// //     console.log("Backend Item Prices:", response);

// //     // Convert the response text into JSON if necessary.
// //     const data =
// //       typeof response === "string"
// //         ? JSON.parse(response)
// //         : response;

// //     // Find the records in the API response.
// //     const records = Array.isArray(data)
// //       ? data
// //       : Array.isArray(data.data)
// //         ? data.data
// //         : Array.isArray(data.items)
// //           ? data.items
// //           : Array.isArray(data.result)
// //             ? data.result
// //             : Array.isArray(data.data?.items)
// //               ? data.data.items
// //               : null;

// //     if (!records) {
// //       console.error("Unexpected API response structure:", data);
// //       return;
// //     }

// //     // Convert backend records into frontend table format.
// //     const formattedItems = records.map(fromDbRow);

// //     // Display the API data in the table.
// //     onItemsChange(formattedItems);

// //     setHasFetched(true);
// //     setCurrentPage(1);

// //     console.log("Formatted Items:", formattedItems);

// //   } catch (error) {
// //     console.error("Fetch API Error:", error);
// //   } finally {
// //     setFetchLoading(false);
// //   }
// // };
// const handleFetch = async () => {
//   try {
//     setFetchLoading(true);

//     const apiResponse = await fetchAllItemPrices();

//     console.log("Complete Backend Response:", apiResponse);

//     // Extract records from the backend response
//     const records = apiResponse?.response?.data;

//     if (!Array.isArray(records)) {
//       console.error("Unexpected API response structure:", apiResponse);
//       return;
//     }

//     // Convert backend fields into frontend table format
//     const formattedItems = records.map((row) => fromDbRow(row));

//     console.log("Formatted Items:", formattedItems);

//     // Display backend records in the existing table
//     onItemsChange(formattedItems);

//     setHasFetched(true);
//     setCurrentPage(1);

//     console.log("Successfully loaded", formattedItems.length, "records");

//   } catch (error) {
//     console.error("Fetch API Error:", error);
//   } finally {
//     setFetchLoading(false);
//   }
// };
// useEffect(() => {
//   handleFetch();
//   // eslint-disable-next-line react-hooks/exhaustive-deps
// }, []);




//   const addItemNo = () =>
//     setItemNoList((previous) => [...previous, ""]);

//   const changeItemNo = (index, value) => {
//     setItemNoList((previous) =>
//       previous.map((item, itemIndex) =>
//         itemIndex === index ? value : item
//       )
//     );
//   };

//   const removeItemNo = (index) => {
//     setItemNoList((previous) =>
//       previous.length === 1
//         ? previous
//         : previous.filter((_, itemIndex) => itemIndex !== index)
//     );
//   };

//   const addFilter = (type) => {
//     if (
//       !type ||
//       filterChips.some((chip) => chip.id === `filter-${type}`)
//     ) {
//       return;
//     }

//     setFilterChips((previous) => [
//       ...previous,
//       {
//         id: `filter-${type}`,
//         type,
//         subType: "customer",
//         value: "",
//       },
//     ]);
//   };

//   const changeFilter = (id, value, subType) => {
//     setFilterChips((previous) =>
//       previous.map((chip) =>
//         chip.id === id
//           ? {
//             ...chip,
//             value,
//             ...(subType ? { subType } : {}),
//           }
//           : chip
//       )
//     );
//   };

//   const removeFilter = (id) => {
//     setFilterChips((previous) =>
//       previous.filter((chip) => chip.id !== id)
//     );
//   };

//   const addNewRow = () => {
//     setNewRows((previous) => [newItem(mode), ...previous]);
//   };

//   const changeNewRow = (id, field, value) => {
//     setNewRows((previous) =>
//       previous.map((row) =>
//         row.id === id ? { ...row, [field]: value } : row
//       )
//     );
//   };

//   const toggleActive = (id, isNew) => {
//     if (isNew) {
//       setNewRows((previous) =>
//         previous.map((row) =>
//           row.id === id ? { ...row, active: !row.active } : row
//         )
//       );

//       return;
//     }

//     const item = modeItems.find((row) => row.id === id);
//     if (!item) return;

//     const current = pendingUpdates[id] || {};
//     const active = !(current.active ?? item.active);

//     setPendingUpdates((previous) => ({
//       ...previous,
//       [id]: {
//         ...previous[id],
//         active,
//         ...(!active ? { endingDate: nowForInput() } : {}),
//       },
//     }));
//   };

//   // Select or deselect all items in the current mode.
//   const toggleAllActive = (checked) => {
//     // Update newly added rows.
//     setNewRows((previous) =>
//       previous.map((row) => ({
//         ...row,
//         active: checked,
//         ...(!checked ? { endingDate: nowForInput() } : {}),
//       }))
//     );

//     // Update existing rows.
//     const updates = {};

//     modeItems.forEach((item) => {
//       updates[item.id] = {
//         ...pendingUpdates[item.id],
//         active: checked,
//         ...(!checked ? { endingDate: nowForInput() } : {}),
//       };
//     });

//     setPendingUpdates((previous) => ({
//       ...previous,
//       ...updates,
//     }));
//   };

//   const updatePending = (id, field, value) => {
//     setPendingUpdates((previous) => ({
//       ...previous,
//       [id]: {
//         ...previous[id],
//         [field]: value,
//       },
//     }));
//   };

//   const validate = (row, isNew) => {
//     const errors = [];
//     const priority = Number(row.priority);

//     ["salesPrice", "lowerLimit", "upperLimit", "minQty"].forEach(
//       (field) => {
//         if (
//           row[field] !== "" &&
//           row[field] != null &&
//           !Number.isFinite(Number(row[field]))
//         ) {
//           errors.push(`${LABELS[field] || field} must be a number`);
//         }
//       }
//     );

//     const sales = Number(row.salesPrice);
//     const lower = Number(row.lowerLimit);
//     const upper = Number(row.upperLimit);

//     if (row.salesPrice !== "" && sales <= 0) {
//       errors.push("Sales Price must be greater than 0");
//     }

//     if (row.lowerLimit !== "" && lower <= 0) {
//       errors.push("Lower Limit must be greater than 0");
//     }

//     if (row.upperLimit !== "" && upper <= 0) {
//       errors.push("Upper Limit must be greater than 0");
//     }

//     if (
//       row.lowerLimit !== "" &&
//       row.upperLimit !== "" &&
//       lower > upper
//     ) {
//       errors.push("Lower Limit cannot be greater than Upper Limit");
//     }

//     if (
//       row.salesPrice !== "" &&
//       row.lowerLimit !== "" &&
//       sales < lower
//     ) {
//       errors.push("Sales Price cannot be less than Lower Limit");
//     }

//     if (
//       row.salesPrice !== "" &&
//       row.upperLimit !== "" &&
//       sales > upper
//     ) {
//       errors.push("Sales Price cannot be greater than Upper Limit");
//     }

//     if (
//       row.startingDate &&
//       row.endingDate &&
//       row.startingDate > row.endingDate
//     ) {
//       errors.push("Starting Date cannot be after Ending Date");
//     }

//     if (isNew) {
//       [
//         "conditionType",
//         "salesPrice",
//         "startingDate",
//         "endingDate",
//         "lowerLimit",
//         "upperLimit",
//         "currency",
//       ].forEach((field) => {
//         if (String(row[field] ?? "").trim() === "") {
//           errors.push(`${LABELS[field] || field} is required`);
//         }
//       });

//       if (
//         !Number.isInteger(priority) ||
//         priority < 1 ||
//         priority > 11
//       ) {
//         errors.push("Priority must be between 1 and 11");
//       } else {
//         PRIORITY_CONFIG[priority - 1].forEach((field) => {
//           if (String(row[field] ?? "").trim() === "") {
//             errors.push(
//               `${LABELS[field] || field} is required for priority ${priority}`
//             );
//           }
//         });
//       }
//     }

//     return errors;
//   };

//   const deleteExisting = (item) => {
//     const confirmed = window.confirm(
//       `Delete item condition for item "${item.itemNo || item.id}"?`
//     );

//     if (!confirmed) return;

//     onItemsChange((previous) =>
//       previous.filter((row) => row.id !== item.id)
//     );

//     setPendingUpdates((previous) => {
//       const next = { ...previous };
//       delete next[item.id];
//       return next;
//     });

//     notify("Item condition deleted from demo data.");
//   };

//   const saveChanges = () => {
//     const newItems = newRows.filter((row) => row.itemNo.trim());

//     for (const row of newItems) {
//       const errors = validate(row, true);

//       if (errors.length) {
//         notify(
//           `Item ${row.itemNo || "(unspecified)"}:\n${errors.join("\n")}`,
//           "error"
//         );

//         return;
//       }
//     }

//     const updates = Object.entries(pendingUpdates);

//     if (!newItems.length && !updates.length) {
//       notify("No changes to save.", "info");
//       return;
//     }

//     const savedNewItems = newItems.map((row) => ({
//       ...row,
//       salesPrice: Number(row.salesPrice),
//       lowerLimit: Number(row.lowerLimit),
//       upperLimit: Number(row.upperLimit),
//       minQty: Number(row.minQty),
//       status: "Success",
//     }));

//     // Display sample JSON payload
//     // console.log(
//     //   "Sample Payload:",
//     //   JSON.stringify(savedNewItems, null, 2)
//     // );

//     onItemsChange((previous) => {
//       const updated = previous.map((item) => {
//         const changes = pendingUpdates[item.id];

//         return changes
//           ? { ...item, ...changes, status: "Success" }
//           : item;
//       });

//       return [...savedNewItems, ...updated];
//     });

//     setNewRows([]);
//     setPendingUpdates({});

//     notify(
//       `${savedNewItems.length} item(s) created and ${updates.length} item(s) updated in demo mode.`
//     );
//   };

//   // FIXED: Export rows as objects and use the correct rowsToCsv arguments.
//   const downloadCsv = () => {
//     try {
//       const headers = COLUMNS.map((column) => column.label);

//       const rows = filteredItems.map((item) => {
//         const pending = pendingUpdates[item.id] || {};

//         return COLUMNS.reduce((row, column) => {
//           row[column.label] =
//             column.type === "active"
//               ? (pending.active ?? item.active)
//                 ? "TRUE"
//                 : "FALSE"
//               : pending[column.key] ?? item[column.key] ?? "";

//           return row;
//         }, {});
//       });

//       const csv = rowsToCsv(rows, headers);

//       saveCsvFile(csv, `${mode}_management.csv`);
//     } catch (error) {
//       console.error("CSV download error:", error);
//       notify("CSV download failed.", "error");
//     }
//   };

//   const startResize = (key, event) => {
//     event.preventDefault();
//     event.stopPropagation();

//     resizingRef.current = {
//       key,
//       startX: event.clientX,
//       startWidth:
//         columnWidths[key] ||
//         COLUMNS.find((column) => column.key === key).width,
//     };

//     document.body.classList.add("dm-col-resizing");
//   };

//   const resetWidths = () => {
//     const reset = {};

//     COLUMNS.forEach((column) => {
//       reset[column.key] = column.width;
//     });

//     setColumnWidths(reset);
//   };

//   const renderNewCell = (row, column) => {
//     const value = row[column.key] ?? "";

//     if (column.type === "select") {
//       return (
//         <select
//           value={value}
//           onChange={(event) =>
//             changeNewRow(row.id, column.key, event.target.value)
//           }
//         >
//           <option value=""></option>

//           {column.options.map((option) => (
//             <option key={option} value={option}>
//               {option}
//             </option>
//           ))}
//         </select>
//       );
//     }

//     if (column.type === "datetime") {
//       return (
//         <input
//           type="datetime-local"
//           step="1"
//           value={inputDate(value)}
//           onChange={(event) =>
//             changeNewRow(
//               row.id,
//               column.key,
//               displayDate(event.target.value)
//             )
//           }
//         />
//       );
//     }

//     return (
//       <input
//         type={column.type === "number" ? "number" : "text"}
//         step={column.type === "number" ? "any" : undefined}
//         placeholder={column.label}
//         value={value}
//         onChange={(event) =>
//           changeNewRow(row.id, column.key, event.target.value)
//         }
//         autoComplete="off"
//       />
//     );
//   };

//   const renderExistingCell = (item, column) => {
//     const pending = pendingUpdates[item.id] || {};
//     const value = pending[column.key] ?? item[column.key] ?? "";

//     const isEditing =
//       editingCell?.id === item.id &&
//       editingCell?.field === column.key;

//     if (column.type === "active") {
//       return (
//         <button
//           type="button"
//           className={`active-tick-btn ${(pending.active ?? item.active) ? "" : "inactive"
//             }`}
//           title="Toggle active"
//           onClick={() => toggleActive(item.id, false)}
//         >
//           {(pending.active ?? item.active) ? "✓" : ""}
//         </button>
//       );
//     }

//     if (!column.editable) return value;

//     if (isEditing) {
//       if (column.type === "select") {
//         return (
//           <select
//             autoFocus
//             value={editingValue}
//             onChange={(event) =>
//               setEditingValue(event.target.value)
//             }
//             onBlur={() => {
//               updatePending(item.id, column.key, editingValue);
//               setEditingCell(null);
//             }}
//           >
//             {column.options.map((option) => (
//               <option key={option} value={option}>
//                 {option}
//               </option>
//             ))}
//           </select>
//         );
//       }

//       return (
//         <input
//           autoFocus
//           type={
//             column.type === "datetime"
//               ? "datetime-local"
//               : column.type === "number"
//                 ? "number"
//                 : "text"
//           }
//           step={
//             column.type === "number" || column.type === "datetime"
//               ? "any"
//               : undefined
//           }
//           value={
//             column.type === "datetime"
//               ? inputDate(editingValue)
//               : editingValue
//           }
//           onChange={(event) =>
//             setEditingValue(
//               column.type === "datetime"
//                 ? displayDate(event.target.value)
//                 : event.target.value
//             )
//           }
//           onBlur={() => {
//             updatePending(item.id, column.key, editingValue);
//             setEditingCell(null);
//           }}
//           onKeyDown={(event) => {
//             if (event.key === "Enter") {
//               updatePending(item.id, column.key, editingValue);
//               setEditingCell(null);
//             }

//             if (event.key === "Escape") {
//               setEditingCell(null);
//             }
//           }}
//         />
//       );
//     }

//     return (
//       <span
//         className="editable-cell"
//         title="Click to edit"
//         onClick={() => {
//           setEditingCell({ id: item.id, field: column.key });
//           setEditingValue(String(value));
//         }}
//       >
//         {value}
//       </span>
//     );
//   };

//   const hasNewRows = newRows.length > 0;

//   // Check whether all items in the current mode are active.
//   const allActive =
//     [...modeItems, ...newRows].length > 0 &&
//     [...modeItems, ...newRows].every((item) => {
//       const pending = pendingUpdates[item.id] || {};
//       return pending.active ?? item.active;
//     });

//   const saveDisabled =
//     !newRows.some((row) => row.itemNo.trim()) &&
//     Object.keys(pendingUpdates).length === 0;

//   // Calculate proportional widths from the user's saved column widths.
//   const totalColumnWidth = COLUMNS.reduce(
//     (total, column) =>
//       total + (columnWidths[column.key] || column.width),
//     0
//   );

//   // Reserve a small amount of space for the Action column when adding rows.
//   const actionColumnWidth = hasNewRows ? 4 : 0;
//   const dataColumnWidth = 100 - actionColumnWidth;

//   return (
//     <div className="item-management-container">
//       <div className="toolbar-form">
//         <div className="filters-row">
//           {/* <div id="itemNoContainer">
//             {itemNoList.map((itemNo, index) => (
//               <div key={index} className="item-no-row">
//                 <input
//                   type="text"
//                   className="itemNoInput"
//                   placeholder="Item No"
//                   value={itemNo}
//                   onChange={(event) =>
//                     changeItemNo(index, event.target.value)
//                   }
//                   autoComplete="off"
//                 />

//                 {index === 0 ? (
//                   <button
//                     type="button"
//                     className="addItemNoBtn"
//                     title="Add Item No"
//                     onClick={addItemNo}
//                   >
//                     +
//                   </button>
//                 ) : (
//                   <button
//                     type="button"
//                     className="removeItemNoBtn"
//                     title="Remove Item No"
//                     onClick={() => removeItemNo(index)}
//                   >
//                     −
//                   </button>
//                 )}
//               </div>
//             ))}
//           </div> */}
//           <div id="itemNoContainer">
//             <div className="item-no-row">
//               <input
//                 type="text"
//                 className="itemNoInput"
//                 placeholder="Item No"
//                 value={itemNoList[0]}
//                 onChange={(event) =>
//                   changeItemNo(0, event.target.value)
//                 }
//                 autoComplete="off"
//               />
//             </div>
//           </div>

//           <div className="core-field">
//             <select
//               id="fetchActive"
//               className="form-control"
//               value={activeFilter}
//               onChange={(event) =>
//                 setActiveFilter(event.target.value)
//               }
//             >
//               <option value="true">Active</option>
//               <option value="false">Inactive</option>
//               <option value="">All</option>
//             </select>
//           </div>

//           <div className="core-field filter-field">
//             <select
//               id="addFilterSelect"
//               className="form-control"
//               value=""
//               onChange={(event) => addFilter(event.target.value)}
//             >
//               <option value="">+ Add filter</option>

//               {FILTER_OPTIONS.map(([value, label]) => (
//                 <option key={value} value={value}>
//                   {label}
//                 </option>
//               ))}
//             </select>
//           </div>

//           <div className="toolbar-actions">
//             <button
//               type="button"
//               id="fetch"
//               className="btn btn-primary"
//               onClick={handleFetch}
//               disabled={fetchLoading}
//             >
//               <FaSearch />
//               {fetchLoading ? "Fetching..." : "Fetch"}
//             </button>

//             <button
//               type="button"
//               id="downloadCsvBtn"
//               className="btn btn-outline"
//               onClick={downloadCsv}
//             >
//               <i className="fas fa-download"></i>
//               <FaDownload />
//               CSV
//             </button>

//             <button
//               type="button"
//               id="importBtnUnique"
//               className="btn btn-outline"
//               onClick={() => onOpenCsv(mode)}
//             >
//               <i className="fas fa-file-import"></i>
//               <FaFileImport />
//               Import
//             </button>

//             <button
//               type="button"
//               id="addItemBtn"
//               className="btn btn-success"
//               onClick={addNewRow}
//             >
//               <i className="fas fa-plus"></i>
//               <FaPlus />
//               Add Item
//             </button>

//             <button
//               type="button"
//               id="saveUpdateBtn"
//               className="btn"
//               disabled={saveDisabled}
//               onClick={saveChanges}
//             >
//               Save
//             </button>
//           </div>
//         </div>

//         {filterChips.length > 0 && (
//           <div id="activeFilters" className="active-filters">
//             {filterChips.map((chip) => {
//               if (chip.type === "customer_group_hierarchy") {
//                 return (
//                   <div
//                     key={chip.id}
//                     className="filter-chip customer-hierarchy-filter"
//                   >
//                     <label className="customer-filter-label">
//                       CUSTOMER
//                     </label>

//                     <select
//                       className="customer-filter-type"
//                       value={chip.subType}
//                       onChange={(event) =>
//                         changeFilter(
//                           chip.id,
//                           chip.value,
//                           event.target.value
//                         )
//                       }
//                     >
//                       <option value="customer">Customer No</option>
//                       <option value="customerGrp">Customer Group</option>
//                       <option value="customerHierarchy">
//                         Customer Hierarchy
//                       </option>
//                     </select>

//                     <input
//                       className="customer-filter-value"
//                       placeholder="Value"
//                       value={chip.value}
//                       onChange={(event) =>
//                         changeFilter(chip.id, event.target.value)
//                       }
//                     />

//                     <button
//                       type="button"
//                       className="customer-filter-remove"
//                       onClick={() => removeFilter(chip.id)}
//                     >
//                       ×
//                     </button>
//                   </div>
//                 );
//               }

//               if (chip.type === "sort_by") {
//                 return (
//                   <div key={chip.id} className="filter-chip">
//                     <label>Sort By</label>

//                     <select
//                       value={chip.value}
//                       onChange={(event) =>
//                         changeFilter(chip.id, event.target.value)
//                       }
//                     >
//                       <option value="">-- Select --</option>
//                       <option value="startingDate">Starting Date</option>
//                       <option value="endingDate">Ending Date</option>
//                       <option value="itemNo">Item No</option>
//                       <option value="salesPrice">Sales Price</option>
//                     </select>

//                     <button
//                       type="button"
//                       className="remove-filter"
//                       onClick={() => removeFilter(chip.id)}
//                     >
//                       ×
//                     </button>
//                   </div>
//                 );
//               }

//               const label =
//                 FILTER_OPTIONS.find(
//                   ([value]) => value === chip.type
//                 )?.[1] || chip.type;

//               const isDate = [
//                 "startingDate",
//                 "endingDate",
//               ].includes(chip.type);

//               const isNumber = [
//                 "salesPrice",
//                 "minQty",
//                 "lowerLimit",
//                 "upperLimit",
//                 "priority",
//               ].includes(chip.type);

//               return (
//                 <div key={chip.id} className="filter-chip">
//                   <label>{label}</label>

//                   <input
//                     type={
//                       isDate
//                         ? "datetime-local"
//                         : isNumber
//                           ? "number"
//                           : "text"
//                     }
//                     placeholder={label}
//                     value={chip.value}
//                     onChange={(event) =>
//                       changeFilter(chip.id, event.target.value)
//                     }
//                   />

//                   <button
//                     type="button"
//                     className="remove-filter"
//                     onClick={() => removeFilter(chip.id)}
//                   >
//                     ×
//                   </button>
//                 </div>
//               );
//             })}
//           </div>
//         )}
//       </div>

//       <div className="results-section">
//         <div
//           className="table-responsive"
//           onPointerDown={startTableDrag}
//         >
//           <table
//             className={`table ${hasNewRows ? "has-new-rows" : ""
//               }`}
//             style={{
//               width: "100%",
//               minWidth: 0,
//               maxWidth: "100%",
//               tableLayout: "fixed",
//             }}
//           >
//             {/* Column widths are proportional, so all columns fit. */}
//             <colgroup>
//               {COLUMNS.map((column) => {
//                 const savedWidth =
//                   columnWidths[column.key] || column.width;

//                 const percentage =
//                   (savedWidth / totalColumnWidth) *
//                   dataColumnWidth;

//                 return (
//                   <col
//                     key={column.key}
//                     style={{
//                       width: `${percentage}%`,
//                     }}
//                   />
//                 );
//               })}

//               {hasNewRows && (
//                 <col
//                   style={{
//                     width: `${actionColumnWidth}%`,
//                   }}
//                 />
//               )}
//             </colgroup>

//             <thead>
//               <tr id="itemPriceTableHead">
//                 {COLUMNS.map((column) => (
//                   <th
//                     key={column.key}
//                     style={{
//                       position: "relative",
//                     }}
//                   >
//                     {column.key === "active" ? (
//                       <div
//                         style={{
//                           display: "flex",
//                           alignItems: "center",
//                           justifyContent: "center",
//                           gap: "4px",
//                         }}
//                       >
//                         <input
//                           type="checkbox"
//                           checked={allActive}
//                           onChange={(event) =>
//                             toggleAllActive(event.target.checked)
//                           }
//                           title="Select All Active"
//                         />

//                         <span>Active</span>
//                       </div>
//                     ) : (
//                       column.label
//                     )}

//                     <div
//                       className="col-resizer"
//                       title="Drag to resize · double-click to reset all"
//                       onPointerDown={(event) =>
//                         startResize(column.key, event)
//                       }
//                       onDoubleClick={resetWidths}
//                     />
//                   </th>
//                 ))}

//                 {hasNewRows && (
//                   <th className="fixed-action-column action-col">
//                     Action
//                   </th>
//                 )}
//               </tr>
//             </thead>

//             <tbody id="itemPriceTableBody">
//               {newRows.map((row) => (
//                 <tr key={row.id} className="new-item-row">
//                   <td>
//                     <button
//                       type="button"
//                       className={`active-tick-btn ${row.active ? "" : "inactive"
//                         }`}
//                       title="Toggle active"
//                       onClick={() => toggleActive(row.id, true)}
//                     >
//                       {row.active ? "✓" : ""}
//                     </button>
//                   </td>

//                   {COLUMNS.slice(1).map((column) => (
//                     <td key={column.key}>
//                       {renderNewCell(row, column)}
//                     </td>
//                   ))}

//                   <td className="action-cell">
//                     <button
//                       type="button"
//                       className="delete-row-btn"
//                       title="Remove row"
//                       onClick={() =>
//                         setNewRows((previous) =>
//                           previous.filter(
//                             (item) => item.id !== row.id
//                           )
//                         )
//                       }
//                     >
//                       ×
//                     </button>
//                   </td>
//                 </tr>
//               ))}

//               {visibleItems.length === 0 && newRows.length === 0 ? (
//                 <tr>
//                   <td
//                     colSpan={COLUMNS.length + (hasNewRows ? 1 : 0)}
//                     className="no-items-cell"
//                   >
//                     No items found
//                   </td>
//                 </tr>
//               ) : (
//                 visibleItems.map((item) => {
//                   const dirty = Boolean(pendingUpdates[item.id]);

//                   return (
//                     <tr
//                       key={item.id}
//                       className={dirty ? "dirty-row" : ""}
//                     >
//                       {COLUMNS.map((column) => (
//                         <td key={column.key}>
//                           {renderExistingCell(item, column)}
//                         </td>
//                       ))}
//                     </tr>
//                   );
//                 })
//               )}
//             </tbody>
//           </table>
//         </div>
//       </div>

//       <div className="pagination-container">
//         <button
//           type="button"
//           disabled={currentPage <= 1}
//           onClick={() =>
//             setCurrentPage((page) => Math.max(1, page - 1))
//           }
//         >
//           Previous
//         </button>

//         <span>
//           Page {currentPage} / {totalPages} &nbsp;·&nbsp;{" "}
//           {filteredItems.length} rows
//         </span>

//         <button
//           type="button"
//           disabled={currentPage >= totalPages}
//           onClick={() =>
//             setCurrentPage((page) =>
//               Math.min(totalPages, page + 1)
//             )
//           }
//         >
//           Next
//         </button>
//       </div>
//     </div>
//   );
// }


























// import { useEffect, useMemo, useRef, useState } from "react";
// import { downloadCsv as saveCsvFile, rowsToCsv } from "../api";


// import {
//   FaSearch,
//   FaDownload,
//   FaFileImport,
//   FaPlus,
// } from "react-icons/fa";

// // const UOM_OPTIONS = ["PAC", "EA", "CAR"];
// const LOCATION_OPTIONS = ["2112", "2113", "2132"];
// // const CURRENCY_OPTIONS = ["AED", "USD", "EUR", "GBP", "JPY", "CAD", "AUD"];
// const PRIORITY_OPTIONS = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11"];

// const COLUMNS = [
//   { key: "active", label: "Active", type: "active", width: 45 },
//   { key: "conditionType", label: "Condition Type", type: "text", width: 95 },
//   { key: "itemNo", label: "Item No", type: "text", width: 80 },
//   { key: "customer", label: "Customer", type: "text", width: 85 },
//   { key: "customerGrp", label: "Customer Grp", type: "text", width: 85 },
//   { key: "customerHierarchy", label: "Customer Hierarchy", type: "text", width: 95 },
//   { key: "distributionChannel", label: "Distribution Channel", type: "text", width: 105 },
//   { key: "locationCode", label: "Location Code", type: "select", options: LOCATION_OPTIONS, width: 90, editable: true },
//   { key: "priority", label: "Priority", type: "select", options: PRIORITY_OPTIONS, width: 65, editable: true },
//   // { key: "currency", label: "Currency", type: "select", options: CURRENCY_OPTIONS, width: 70, editable: true },
//   { key: "currency", label: "Currency", type: "text", width: 70, editable: true },
//   { key: "salesPrice", label: "Sales Price", type: "number", width: 80, editable: true },
//   // { key: "uom", label: "UOM", type: "select", options: UOM_OPTIONS, width: 60, editable: true },
//   { key: "uom", label: "UOM", type: "text", width: 60, editable: true },
//   { key: "minQty", label: "Min Qty", type: "number", width: 65, editable: true },
//   { key: "startingDate", label: "Starting Date", type: "datetime", width: 145, editable: true },
//   { key: "endingDate", label: "Ending Date", type: "datetime", width: 145, editable: true },
//   { key: "lowerLimit", label: "Lower Limit", type: "number", width: 80, editable: true },
//   { key: "upperLimit", label: "Upper Limit", type: "number", width: 80, editable: true },
//   { key: "zoneCode", label: "Zone Code", type: "text", width: 85, editable: true },
//   { key: "offerArticle", label: "Offer Article", type: "text", width: 85, editable: true },
// ];

// const FILTER_OPTIONS = [
//   ["customer_group_hierarchy", "Customer / Group / Hierarchy"],
//   ["sort_by", "Sort By"],
//   ["salesOrganization", "Sales Organization"],
//   ["distributionChannel", "Distribution Channel"],
//   ["locationCode", "Location Code"],
//   ["conditionType", "Condition Type"],
//   ["salesPrice", "Sales Price"],
//   ["currency", "Currency"],
//   ["uom", "Unit of Measure"],
//   ["minQty", "Minimum Quantity"],
//   ["lowerLimit", "Lower Limit"],
//   ["upperLimit", "Upper Limit"],
//   ["zoneCode", "Transportation Zone"],
//   ["startingDate", "Starting Date"],
//   ["endingDate", "Ending Date"],
//   ["priority", "Priority"],
//   ["offerArticle", "Offer Article"],
// ];

// const PRIORITY_CONFIG = [
//   ["distributionChannel", "customer", "locationCode", "itemNo", "uom"],
//   ["distributionChannel", "customerGrp", "locationCode", "itemNo", "uom"],
//   ["distributionChannel", "customer", "itemNo", "uom"],
//   ["distributionChannel", "customerGrp", "itemNo", "uom"],
//   ["customerGrp", "itemNo", "uom"],
//   ["customerHierarchy", "locationCode", "itemNo", "uom"],
//   ["customerHierarchy", "itemNo", "uom"],
//   ["distributionChannel", "locationCode", "itemNo", "zoneCode", "uom"],
//   ["distributionChannel", "locationCode", "itemNo", "uom"],
//   ["distributionChannel", "itemNo", "uom"],
//   ["itemNo", "uom"],
// ];

// const LABELS = {
//   conditionType: "Condition Type",
//   salesPrice: "Sales Price",
//   startingDate: "Starting Date",
//   endingDate: "Ending Date",
//   lowerLimit: "Lower Limit",
//   upperLimit: "Upper Limit",
//   priority: "Priority",
//   currency: "Currency",
//   distributionChannel: "Distribution Channel",
//   customer: "Customer No",
//   customerGrp: "Customer Group",
//   customerHierarchy: "Customer Hierarchy",
//   locationCode: "Location Code",
//   itemNo: "Item No",
//   uom: "Unit of Measure",
//   zoneCode: "Transportation Zone Code",
// };

// function nowForInput() {
//   const date = new Date(Date.now() - new Date().getTimezoneOffset() * 60000);
//   return date.toISOString().slice(0, 19).replace("T", " ");
// }

// function endOfTodayForInput() {
//   const date = new Date();
//   const year = date.getFullYear();
//   const month = String(date.getMonth() + 1).padStart(2, "0");
//   const day = String(date.getDate()).padStart(2, "0");
//   return `${year}-${month}-${day} 23:59:59`;
// }

// function inputDate(value) {
//   return value ? String(value).replace(" ", "T").slice(0, 19) : "";
// }

// function displayDate(value) {
//   return value ? String(value).replace("T", " ") : "";
// }

// function newItem(mode) {
//   return {
//     id: `new-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
//     active: true,
//     conditionType: mode === "discount" ? "ZDIS" : "ZEN1",
//     itemNo: "",
//     customer: "",
//     customerGrp: "",
//     customerHierarchy: "",
//     distributionChannel: "10",
//     locationCode: "2112",
//     priority: "1",
//     currency: "AED",
//     salesPrice: "",
//     uom: "PAC",
//     minQty: "1",
//     startingDate: nowForInput(),
//     endingDate: endOfTodayForInput(),
//     lowerLimit: "",
//     upperLimit: "",
//     zoneCode: "",
//     offerArticle: "No",
//   };
// }

// export function ItemManagementView({
//   mode,
//   items = [],
//   onItemsChange,
//   onOpenCsv,
//   onNotify,
// }) {
//   const [itemNoList, setItemNoList] = useState([""]);
//   const [activeFilter, setActiveFilter] = useState("true");
//   const [filterChips, setFilterChips] = useState([]);
//   const [newRows, setNewRows] = useState([]);
//   const [pendingUpdates, setPendingUpdates] = useState({});
//   const [currentPage, setCurrentPage] = useState(1);
//   const [editingCell, setEditingCell] = useState(null);
//   const [editingValue, setEditingValue] = useState("");
//   const [columnWidths, setColumnWidths] = useState({});
//   const [hasFetched, setHasFetched] = useState(false);

//   const resizingRef = useRef(null);
//   const dragScrollRef = useRef(null);

//   const pageSize = 500;
//   const storageKey = `jh_col_widths_${mode}`;

//   // Load saved column widths.
//   useEffect(() => {
//     try {
//       const saved = JSON.parse(localStorage.getItem(storageKey) || "{}");
//       const initial = {};

//       COLUMNS.forEach((column) => {
//         initial[column.key] = saved[column.key] || column.width;
//       });

//       setColumnWidths(initial);
//     } catch {
//       const initial = {};

//       COLUMNS.forEach((column) => {
//         initial[column.key] = column.width;
//       });

//       setColumnWidths(initial);
//     }
//   }, [storageKey]);

//   // Save column widths.
//   useEffect(() => {
//     if (!Object.keys(columnWidths).length) return;
//     localStorage.setItem(storageKey, JSON.stringify(columnWidths));
//   }, [columnWidths, storageKey]);

//   // Column resizing.
//   useEffect(() => {
//     const move = (event) => {
//       if (!resizingRef.current) return;

//       const { key, startX, startWidth } = resizingRef.current;

//       setColumnWidths((previous) => ({
//         ...previous,
//         [key]: Math.max(30, startWidth + event.clientX - startX),
//       }));
//     };

//     const stop = () => {
//       resizingRef.current = null;
//       document.body.classList.remove("dm-col-resizing");
//     };

//     window.addEventListener("pointermove", move);
//     window.addEventListener("pointerup", stop);

//     return () => {
//       window.removeEventListener("pointermove", move);
//       window.removeEventListener("pointerup", stop);
//     };
//   }, []);

//   // Excel-style click-and-drag scrolling.
//   const startTableDrag = (event) => {
//     if (event.button !== 0) return;

//     if (
//       event.target.closest(
//         "input, select, textarea, button, a, .col-resizer, .editable-cell"
//       )
//     ) {
//       return;
//     }

//     const container = event.currentTarget;

//     dragScrollRef.current = {
//       container,
//       startX: event.clientX,
//       startY: event.clientY,
//       scrollLeft: container.scrollLeft,
//       scrollTop: container.scrollTop,
//       isDragging: false,
//     };
//   };

//   useEffect(() => {
//     const handleDragMove = (event) => {
//       const drag = dragScrollRef.current;
//       if (!drag) return;

//       const deltaX = event.clientX - drag.startX;
//       const deltaY = event.clientY - drag.startY;

//       if (
//         !drag.isDragging &&
//         (Math.abs(deltaX) > 4 || Math.abs(deltaY) > 4)
//       ) {
//         drag.isDragging = true;
//         document.body.classList.add("dm-table-dragging");
//       }

//       if (!drag.isDragging) return;

//       event.preventDefault();

//       drag.container.scrollLeft = drag.scrollLeft - deltaX;
//       drag.container.scrollTop = drag.scrollTop - deltaY;
//     };

//     const stopTableDrag = () => {
//       if (dragScrollRef.current?.isDragging) {
//         document.body.classList.remove("dm-table-dragging");
//       }

//       dragScrollRef.current = null;
//     };

//     window.addEventListener("pointermove", handleDragMove);
//     window.addEventListener("pointerup", stopTableDrag);
//     window.addEventListener("pointercancel", stopTableDrag);

//     return () => {
//       window.removeEventListener("pointermove", handleDragMove);
//       window.removeEventListener("pointerup", stopTableDrag);
//       window.removeEventListener("pointercancel", stopTableDrag);
//       document.body.classList.remove("dm-table-dragging");
//     };
//   }, []);

//   const notify = (message, type = "success") => {
//     onNotify?.(message, type);
//   };

//   const modeItems = useMemo(
//     () =>
//       items.filter((item) =>
//         mode === "discount"
//           ? item.conditionType === "ZDIS"
//           : item.conditionType !== "ZDIS"
//       ),
//     [items, mode]
//   );

//   const filteredItems = useMemo(() => {
//     let result = [...modeItems];

//     const itemNumbers = itemNoList
//       .map((value) => value.trim().toLowerCase())
//       .filter(Boolean);

//     if (hasFetched && itemNumbers.length) {
//       result = result.filter((item) =>
//         itemNumbers.some((number) =>
//           String(item.itemNo || "").toLowerCase().includes(number)
//         )
//       );
//     }

//     if (hasFetched && activeFilter !== "") {
//       result = result.filter(
//         (item) => Boolean(item.active) === (activeFilter === "true")
//       );
//     }

//     filterChips.forEach((chip) => {
//       if (!chip.value) return;

//       const field =
//         chip.type === "customer_group_hierarchy"
//           ? chip.subType
//           : chip.type;

//       if (chip.type === "sort_by") {
//         result.sort((a, b) =>
//           String(a[chip.value] || "").localeCompare(
//             String(b[chip.value] || ""),
//             undefined,
//             { numeric: true }
//           )
//         );

//         return;
//       }

//       result = result.filter((item) =>
//         String(item[field] ?? "")
//           .toLowerCase()
//           .includes(String(chip.value).toLowerCase())
//       );
//     });

//     return result;
//   }, [modeItems, itemNoList, activeFilter, filterChips, hasFetched]);

//   const totalPages = Math.max(
//     1,
//     Math.ceil(filteredItems.length / pageSize)
//   );

//   const visibleItems = filteredItems.slice(
//     (currentPage - 1) * pageSize,
//     currentPage * pageSize
//   );

//   const handleFetch = () => {
//     setHasFetched(true);
//     setCurrentPage(1);
//   };

//   const addItemNo = () =>
//     setItemNoList((previous) => [...previous, ""]);

//   const changeItemNo = (index, value) => {
//     setItemNoList((previous) =>
//       previous.map((item, itemIndex) =>
//         itemIndex === index ? value : item
//       )
//     );
//   };

//   const removeItemNo = (index) => {
//     setItemNoList((previous) =>
//       previous.length === 1
//         ? previous
//         : previous.filter((_, itemIndex) => itemIndex !== index)
//     );
//   };

//   const addFilter = (type) => {
//     if (
//       !type ||
//       filterChips.some((chip) => chip.id === `filter-${type}`)
//     ) {
//       return;
//     }

//     setFilterChips((previous) => [
//       ...previous,
//       {
//         id: `filter-${type}`,
//         type,
//         subType: "customer",
//         value: "",
//       },
//     ]);
//   };

//   const changeFilter = (id, value, subType) => {
//     setFilterChips((previous) =>
//       previous.map((chip) =>
//         chip.id === id
//           ? {
//             ...chip,
//             value,
//             ...(subType ? { subType } : {}),
//           }
//           : chip
//       )
//     );
//   };

//   const removeFilter = (id) => {
//     setFilterChips((previous) =>
//       previous.filter((chip) => chip.id !== id)
//     );
//   };

//   const addNewRow = () => {
//     setNewRows((previous) => [newItem(mode), ...previous]);
//   };

//   const changeNewRow = (id, field, value) => {
//     setNewRows((previous) =>
//       previous.map((row) =>
//         row.id === id ? { ...row, [field]: value } : row
//       )
//     );
//   };

//   const toggleActive = (id, isNew) => {
//     if (isNew) {
//       setNewRows((previous) =>
//         previous.map((row) =>
//           row.id === id ? { ...row, active: !row.active } : row
//         )
//       );

//       return;
//     }

//     const item = modeItems.find((row) => row.id === id);
//     if (!item) return;

//     const current = pendingUpdates[id] || {};
//     const active = !(current.active ?? item.active);

//     setPendingUpdates((previous) => ({
//       ...previous,
//       [id]: {
//         ...previous[id],
//         active,
//         ...(!active ? { endingDate: nowForInput() } : {}),
//       },
//     }));
//   };

//   // Select or deselect all items in the current mode.
//   const toggleAllActive = (checked) => {
//     // Update newly added rows.
//     setNewRows((previous) =>
//       previous.map((row) => ({
//         ...row,
//         active: checked,
//         ...(!checked ? { endingDate: nowForInput() } : {}),
//       }))
//     );

//     // Update existing rows.
//     const updates = {};

//     modeItems.forEach((item) => {
//       updates[item.id] = {
//         ...pendingUpdates[item.id],
//         active: checked,
//         ...(!checked ? { endingDate: nowForInput() } : {}),
//       };
//     });

//     setPendingUpdates((previous) => ({
//       ...previous,
//       ...updates,
//     }));
//   };

//   const updatePending = (id, field, value) => {
//     setPendingUpdates((previous) => ({
//       ...previous,
//       [id]: {
//         ...previous[id],
//         [field]: value,
//       },
//     }));
//   };

//   const validate = (row, isNew) => {
//     const errors = [];
//     const priority = Number(row.priority);

//     ["salesPrice", "lowerLimit", "upperLimit", "minQty"].forEach(
//       (field) => {
//         if (
//           row[field] !== "" &&
//           row[field] != null &&
//           !Number.isFinite(Number(row[field]))
//         ) {
//           errors.push(`${LABELS[field] || field} must be a number`);
//         }
//       }
//     );

//     const sales = Number(row.salesPrice);
//     const lower = Number(row.lowerLimit);
//     const upper = Number(row.upperLimit);

//     if (row.salesPrice !== "" && sales <= 0) {
//       errors.push("Sales Price must be greater than 0");
//     }

//     if (row.lowerLimit !== "" && lower <= 0) {
//       errors.push("Lower Limit must be greater than 0");
//     }

//     if (row.upperLimit !== "" && upper <= 0) {
//       errors.push("Upper Limit must be greater than 0");
//     }

//     if (
//       row.lowerLimit !== "" &&
//       row.upperLimit !== "" &&
//       lower > upper
//     ) {
//       errors.push("Lower Limit cannot be greater than Upper Limit");
//     }

//     if (
//       row.salesPrice !== "" &&
//       row.lowerLimit !== "" &&
//       sales < lower
//     ) {
//       errors.push("Sales Price cannot be less than Lower Limit");
//     }

//     if (
//       row.salesPrice !== "" &&
//       row.upperLimit !== "" &&
//       sales > upper
//     ) {
//       errors.push("Sales Price cannot be greater than Upper Limit");
//     }

//     if (
//       row.startingDate &&
//       row.endingDate &&
//       row.startingDate > row.endingDate
//     ) {
//       errors.push("Starting Date cannot be after Ending Date");
//     }

//     if (isNew) {
//       [
//         "conditionType",
//         "salesPrice",
//         "startingDate",
//         "endingDate",
//         "lowerLimit",
//         "upperLimit",
//         "currency",
//       ].forEach((field) => {
//         if (String(row[field] ?? "").trim() === "") {
//           errors.push(`${LABELS[field] || field} is required`);
//         }
//       });

//       if (
//         !Number.isInteger(priority) ||
//         priority < 1 ||
//         priority > 11
//       ) {
//         errors.push("Priority must be between 1 and 11");
//       } else {
//         PRIORITY_CONFIG[priority - 1].forEach((field) => {
//           if (String(row[field] ?? "").trim() === "") {
//             errors.push(
//               `${LABELS[field] || field} is required for priority ${priority}`
//             );
//           }
//         });
//       }
//     }

//     return errors;
//   };

//   const deleteExisting = (item) => {
//     const confirmed = window.confirm(
//       `Delete item condition for item "${item.itemNo || item.id}"?`
//     );

//     if (!confirmed) return;

//     onItemsChange((previous) =>
//       previous.filter((row) => row.id !== item.id)
//     );

//     setPendingUpdates((previous) => {
//       const next = { ...previous };
//       delete next[item.id];
//       return next;
//     });

//     notify("Item condition deleted from demo data.");
//   };

//   const saveChanges = () => {
//     const newItems = newRows.filter((row) => row.itemNo.trim());

//     for (const row of newItems) {
//       const errors = validate(row, true);

//       if (errors.length) {
//         notify(
//           `Item ${row.itemNo || "(unspecified)"}:\n${errors.join("\n")}`,
//           "error"
//         );

//         return;
//       }
//     }

//     const updates = Object.entries(pendingUpdates);

//     if (!newItems.length && !updates.length) {
//       notify("No changes to save.", "info");
//       return;
//     }

//     const savedNewItems = newItems.map((row) => ({
//       ...row,
//       salesPrice: Number(row.salesPrice),
//       lowerLimit: Number(row.lowerLimit),
//       upperLimit: Number(row.upperLimit),
//       minQty: Number(row.minQty),
//       status: "Success",
//     }));

//     // Display sample JSON payload
// // console.log(
// //   "Sample Payload:",
// //   JSON.stringify(savedNewItems, null, 2)
// // );

//     onItemsChange((previous) => {
//       const updated = previous.map((item) => {
//         const changes = pendingUpdates[item.id];

//         return changes
//           ? { ...item, ...changes, status: "Success" }
//           : item;
//       });

//       return [...savedNewItems, ...updated];
//     });

//     setNewRows([]);
//     setPendingUpdates({});

//     notify(
//       `${savedNewItems.length} item(s) created and ${updates.length} item(s) updated in demo mode.`
//     );
//   };

//   // FIXED: Export rows as objects and use the correct rowsToCsv arguments.
//   const downloadCsv = () => {
//     try {
//       const headers = COLUMNS.map((column) => column.label);

//       const rows = filteredItems.map((item) => {
//         const pending = pendingUpdates[item.id] || {};

//         return COLUMNS.reduce((row, column) => {
//           row[column.label] =
//             column.type === "active"
//               ? (pending.active ?? item.active)
//                 ? "TRUE"
//                 : "FALSE"
//               : pending[column.key] ?? item[column.key] ?? "";

//           return row;
//         }, {});
//       });

//       const csv = rowsToCsv(rows, headers);

//       saveCsvFile(csv, `${mode}_management.csv`);
//     } catch (error) {
//       console.error("CSV download error:", error);
//       notify("CSV download failed.", "error");
//     }
//   };

//   const startResize = (key, event) => {
//     event.preventDefault();
//     event.stopPropagation();

//     resizingRef.current = {
//       key,
//       startX: event.clientX,
//       startWidth:
//         columnWidths[key] ||
//         COLUMNS.find((column) => column.key === key).width,
//     };

//     document.body.classList.add("dm-col-resizing");
//   };

//   const resetWidths = () => {
//     const reset = {};

//     COLUMNS.forEach((column) => {
//       reset[column.key] = column.width;
//     });

//     setColumnWidths(reset);
//   };

//   const renderNewCell = (row, column) => {
//     const value = row[column.key] ?? "";

//     if (column.type === "select") {
//       return (
//         <select
//           value={value}
//           onChange={(event) =>
//             changeNewRow(row.id, column.key, event.target.value)
//           }
//         >
//           <option value=""></option>

//           {column.options.map((option) => (
//             <option key={option} value={option}>
//               {option}
//             </option>
//           ))}
//         </select>
//       );
//     }

//     if (column.type === "datetime") {
//       return (
//         <input
//           type="datetime-local"
//           step="1"
//           value={inputDate(value)}
//           onChange={(event) =>
//             changeNewRow(
//               row.id,
//               column.key,
//               displayDate(event.target.value)
//             )
//           }
//         />
//       );
//     }

//     return (
//       <input
//         type={column.type === "number" ? "number" : "text"}
//         step={column.type === "number" ? "any" : undefined}
//         placeholder={column.label}
//         value={value}
//         onChange={(event) =>
//           changeNewRow(row.id, column.key, event.target.value)
//         }
//         autoComplete="off"
//       />
//     );
//   };

//   const renderExistingCell = (item, column) => {
//     const pending = pendingUpdates[item.id] || {};
//     const value = pending[column.key] ?? item[column.key] ?? "";

//     const isEditing =
//       editingCell?.id === item.id &&
//       editingCell?.field === column.key;

//     if (column.type === "active") {
//       return (
//         <button
//           type="button"
//           className={`active-tick-btn ${(pending.active ?? item.active) ? "" : "inactive"
//             }`}
//           title="Toggle active"
//           onClick={() => toggleActive(item.id, false)}
//         >
//           {(pending.active ?? item.active) ? "✓" : ""}
//         </button>
//       );
//     }

//     if (!column.editable) return value;

//     if (isEditing) {
//       if (column.type === "select") {
//         return (
//           <select
//             autoFocus
//             value={editingValue}
//             onChange={(event) =>
//               setEditingValue(event.target.value)
//             }
//             onBlur={() => {
//               updatePending(item.id, column.key, editingValue);
//               setEditingCell(null);
//             }}
//           >
//             {column.options.map((option) => (
//               <option key={option} value={option}>
//                 {option}
//               </option>
//             ))}
//           </select>
//         );
//       }

//       return (
//         <input
//           autoFocus
//           type={
//             column.type === "datetime"
//               ? "datetime-local"
//               : column.type === "number"
//                 ? "number"
//                 : "text"
//           }
//           step={
//             column.type === "number" || column.type === "datetime"
//               ? "any"
//               : undefined
//           }
//           value={
//             column.type === "datetime"
//               ? inputDate(editingValue)
//               : editingValue
//           }
//           onChange={(event) =>
//             setEditingValue(
//               column.type === "datetime"
//                 ? displayDate(event.target.value)
//                 : event.target.value
//             )
//           }
//           onBlur={() => {
//             updatePending(item.id, column.key, editingValue);
//             setEditingCell(null);
//           }}
//           onKeyDown={(event) => {
//             if (event.key === "Enter") {
//               updatePending(item.id, column.key, editingValue);
//               setEditingCell(null);
//             }

//             if (event.key === "Escape") {
//               setEditingCell(null);
//             }
//           }}
//         />
//       );
//     }

//     return (
//       <span
//         className="editable-cell"
//         title="Click to edit"
//         onClick={() => {
//           setEditingCell({ id: item.id, field: column.key });
//           setEditingValue(String(value));
//         }}
//       >
//         {value}
//       </span>
//     );
//   };

//   const hasNewRows = newRows.length > 0;

//   // Check whether all items in the current mode are active.
//   const allActive =
//     [...modeItems, ...newRows].length > 0 &&
//     [...modeItems, ...newRows].every((item) => {
//       const pending = pendingUpdates[item.id] || {};
//       return pending.active ?? item.active;
//     });

//   const saveDisabled =
//     !newRows.some((row) => row.itemNo.trim()) &&
//     Object.keys(pendingUpdates).length === 0;

//   // Calculate proportional widths from the user's saved column widths.
//   const totalColumnWidth = COLUMNS.reduce(
//     (total, column) =>
//       total + (columnWidths[column.key] || column.width),
//     0
//   );

//   // Reserve a small amount of space for the Action column when adding rows.
//   const actionColumnWidth = hasNewRows ? 4 : 0;
//   const dataColumnWidth = 100 - actionColumnWidth;

//   return (
//     <div className="item-management-container">
//       <div className="toolbar-form">
//         <div className="filters-row">
//           {/* <div id="itemNoContainer">
//             {itemNoList.map((itemNo, index) => (
//               <div key={index} className="item-no-row">
//                 <input
//                   type="text"
//                   className="itemNoInput"
//                   placeholder="Item No"
//                   value={itemNo}
//                   onChange={(event) =>
//                     changeItemNo(index, event.target.value)
//                   }
//                   autoComplete="off"
//                 />

//                 {index === 0 ? (
//                   <button
//                     type="button"
//                     className="addItemNoBtn"
//                     title="Add Item No"
//                     onClick={addItemNo}
//                   >
//                     +
//                   </button>
//                 ) : (
//                   <button
//                     type="button"
//                     className="removeItemNoBtn"
//                     title="Remove Item No"
//                     onClick={() => removeItemNo(index)}
//                   >
//                     −
//                   </button>
//                 )}
//               </div>
//             ))}
//           </div> */}
//           <div id="itemNoContainer">
//             <div className="item-no-row">
//               <input
//                 type="text"
//                 className="itemNoInput"
//                 placeholder="Item No"
//                 value={itemNoList[0]}
//                 onChange={(event) =>
//                   changeItemNo(0, event.target.value)
//                 }
//                 autoComplete="off"
//               />
//             </div>
//           </div>

//           <div className="core-field">
//             <select
//               id="fetchActive"
//               className="form-control"
//               value={activeFilter}
//               onChange={(event) =>
//                 setActiveFilter(event.target.value)
//               }
//             >
//               <option value="true">Active</option>
//               <option value="false">Inactive</option>
//               <option value="">All</option>
//             </select>
//           </div>

//           <div className="core-field filter-field">
//             <select
//               id="addFilterSelect"
//               className="form-control"
//               value=""
//               onChange={(event) => addFilter(event.target.value)}
//             >
//               <option value="">+ Add filter</option>

//               {FILTER_OPTIONS.map(([value, label]) => (
//                 <option key={value} value={value}>
//                   {label}
//                 </option>
//               ))}
//             </select>
//           </div>

//           <div className="toolbar-actions">
//             <button
//               type="button"
//               id="fetch"
//               className="btn btn-primary"
//               onClick={handleFetch}
//             >
//               <i className="fas fa-search"></i>
//               <FaSearch />
//               Fetch
//             </button>

//             <button
//               type="button"
//               id="downloadCsvBtn"
//               className="btn btn-outline"
//               onClick={downloadCsv}
//             >
//               <i className="fas fa-download"></i>
//               <FaDownload />
//               CSV
//             </button>

//             <button
//               type="button"
//               id="importBtnUnique"
//               className="btn btn-outline"
//               onClick={() => onOpenCsv(mode)}
//             >
//               <i className="fas fa-file-import"></i>
//               <FaFileImport />
//               Import
//             </button>

//             <button
//               type="button"
//               id="addItemBtn"
//               className="btn btn-success"
//               onClick={addNewRow}
//             >
//               <i className="fas fa-plus"></i>
//               <FaPlus />
//               Add Item
//             </button>

//             <button
//               type="button"
//               id="saveUpdateBtn"
//               className="btn"
//               disabled={saveDisabled}
//               onClick={saveChanges}
//             >
//               Save
//             </button>
//           </div>
//         </div>

//         {filterChips.length > 0 && (
//           <div id="activeFilters" className="active-filters">
//             {filterChips.map((chip) => {
//               if (chip.type === "customer_group_hierarchy") {
//                 return (
//                   <div
//                     key={chip.id}
//                     className="filter-chip customer-hierarchy-filter"
//                   >
//                     <label className="customer-filter-label">
//                       CUSTOMER
//                     </label>

//                     <select
//                       className="customer-filter-type"
//                       value={chip.subType}
//                       onChange={(event) =>
//                         changeFilter(
//                           chip.id,
//                           chip.value,
//                           event.target.value
//                         )
//                       }
//                     >
//                       <option value="customer">Customer No</option>
//                       <option value="customerGrp">Customer Group</option>
//                       <option value="customerHierarchy">
//                         Customer Hierarchy
//                       </option>
//                     </select>

//                     <input
//                       className="customer-filter-value"
//                       placeholder="Value"
//                       value={chip.value}
//                       onChange={(event) =>
//                         changeFilter(chip.id, event.target.value)
//                       }
//                     />

//                     <button
//                       type="button"
//                       className="customer-filter-remove"
//                       onClick={() => removeFilter(chip.id)}
//                     >
//                       ×
//                     </button>
//                   </div>
//                 );
//               }

//               if (chip.type === "sort_by") {
//                 return (
//                   <div key={chip.id} className="filter-chip">
//                     <label>Sort By</label>

//                     <select
//                       value={chip.value}
//                       onChange={(event) =>
//                         changeFilter(chip.id, event.target.value)
//                       }
//                     >
//                       <option value="">-- Select --</option>
//                       <option value="startingDate">Starting Date</option>
//                       <option value="endingDate">Ending Date</option>
//                       <option value="itemNo">Item No</option>
//                       <option value="salesPrice">Sales Price</option>
//                     </select>

//                     <button
//                       type="button"
//                       className="remove-filter"
//                       onClick={() => removeFilter(chip.id)}
//                     >
//                       ×
//                     </button>
//                   </div>
//                 );
//               }

//               const label =
//                 FILTER_OPTIONS.find(
//                   ([value]) => value === chip.type
//                 )?.[1] || chip.type;

//               const isDate = [
//                 "startingDate",
//                 "endingDate",
//               ].includes(chip.type);

//               const isNumber = [
//                 "salesPrice",
//                 "minQty",
//                 "lowerLimit",
//                 "upperLimit",
//                 "priority",
//               ].includes(chip.type);

//               return (
//                 <div key={chip.id} className="filter-chip">
//                   <label>{label}</label>

//                   <input
//                     type={
//                       isDate
//                         ? "datetime-local"
//                         : isNumber
//                           ? "number"
//                           : "text"
//                     }
//                     placeholder={label}
//                     value={chip.value}
//                     onChange={(event) =>
//                       changeFilter(chip.id, event.target.value)
//                     }
//                   />

//                   <button
//                     type="button"
//                     className="remove-filter"
//                     onClick={() => removeFilter(chip.id)}
//                   >
//                     ×
//                   </button>
//                 </div>
//               );
//             })}
//           </div>
//         )}
//       </div>

//       <div className="results-section">
//         <div
//           className="table-responsive"
//           onPointerDown={startTableDrag}
//         >
//           <table
//             className={`table ${hasNewRows ? "has-new-rows" : ""
//               }`}
//             style={{
//               width: "100%",
//               minWidth: 0,
//               maxWidth: "100%",
//               tableLayout: "fixed",
//             }}
//           >
//             {/* Column widths are proportional, so all columns fit. */}
//             <colgroup>
//               {COLUMNS.map((column) => {
//                 const savedWidth =
//                   columnWidths[column.key] || column.width;

//                 const percentage =
//                   (savedWidth / totalColumnWidth) *
//                   dataColumnWidth;

//                 return (
//                   <col
//                     key={column.key}
//                     style={{
//                       width: `${percentage}%`,
//                     }}
//                   />
//                 );
//               })}

//               {hasNewRows && (
//                 <col
//                   style={{
//                     width: `${actionColumnWidth}%`,
//                   }}
//                 />
//               )}
//             </colgroup>

//             <thead>
//               <tr id="itemPriceTableHead">
//                 {COLUMNS.map((column) => (
//                   <th
//                     key={column.key}
//                     style={{
//                       position: "relative",
//                     }}
//                   >
//                     {column.key === "active" ? (
//                       <div
//                         style={{
//                           display: "flex",
//                           alignItems: "center",
//                           justifyContent: "center",
//                           gap: "4px",
//                         }}
//                       >
//                         <input
//                           type="checkbox"
//                           checked={allActive}
//                           onChange={(event) =>
//                             toggleAllActive(event.target.checked)
//                           }
//                           title="Select All Active"
//                         />

//                         <span>Active</span>
//                       </div>
//                     ) : (
//                       column.label
//                     )}

//                     <div
//                       className="col-resizer"
//                       title="Drag to resize · double-click to reset all"
//                       onPointerDown={(event) =>
//                         startResize(column.key, event)
//                       }
//                       onDoubleClick={resetWidths}
//                     />
//                   </th>
//                 ))}

//                 {hasNewRows && (
//                   <th className="fixed-action-column action-col">
//                     Action
//                   </th>
//                 )}
//               </tr>
//             </thead>

//             <tbody id="itemPriceTableBody">
//               {newRows.map((row) => (
//                 <tr key={row.id} className="new-item-row">
//                   <td>
//                     <button
//                       type="button"
//                       className={`active-tick-btn ${row.active ? "" : "inactive"
//                         }`}
//                       title="Toggle active"
//                       onClick={() => toggleActive(row.id, true)}
//                     >
//                       {row.active ? "✓" : ""}
//                     </button>
//                   </td>

//                   {COLUMNS.slice(1).map((column) => (
//                     <td key={column.key}>
//                       {renderNewCell(row, column)}
//                     </td>
//                   ))}

//                   <td className="action-cell">
//                     <button
//                       type="button"
//                       className="delete-row-btn"
//                       title="Remove row"
//                       onClick={() =>
//                         setNewRows((previous) =>
//                           previous.filter(
//                             (item) => item.id !== row.id
//                           )
//                         )
//                       }
//                     >
//                       ×
//                     </button>
//                   </td>
//                 </tr>
//               ))}

//               {visibleItems.length === 0 && newRows.length === 0 ? (
//                 <tr>
//                   <td
//                     colSpan={COLUMNS.length + (hasNewRows ? 1 : 0)}
//                     className="no-items-cell"
//                   >
//                     No items found
//                   </td>
//                 </tr>
//               ) : (
//                 visibleItems.map((item) => {
//                   const dirty = Boolean(pendingUpdates[item.id]);

//                   return (
//                     <tr
//                       key={item.id}
//                       className={dirty ? "dirty-row" : ""}
//                     >
//                       {COLUMNS.map((column) => (
//                         <td key={column.key}>
//                           {renderExistingCell(item, column)}
//                         </td>
//                       ))}
//                     </tr>
//                   );
//                 })
//               )}
//             </tbody>
//           </table>
//         </div>
//       </div>

//       <div className="pagination-container">
//         <button
//           type="button"
//           disabled={currentPage <= 1}
//           onClick={() =>
//             setCurrentPage((page) => Math.max(1, page - 1))
//           }
//         >
//           Previous
//         </button>

//         <span>
//           Page {currentPage} / {totalPages} &nbsp;·&nbsp;{" "}
//           {filteredItems.length} rows
//         </span>

//         <button
//           type="button"
//           disabled={currentPage >= totalPages}
//           onClick={() =>
//             setCurrentPage((page) =>
//               Math.min(totalPages, page + 1)
//             )
//           }
//         >
//           Next
//         </button>
//       </div>
//     </div>
//   );
// }





