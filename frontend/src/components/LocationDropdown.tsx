"use client";

import { useState, useRef, useEffect } from "react";
import styles from "./LocationDropdown.module.css";

interface LocationDropdownProps {
  locations: string[];
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
}

export default function LocationDropdown({
  locations,
  value,
  onChange,
  placeholder = "Search for a city or area…",
}: LocationDropdownProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [search, setSearch] = useState("");
  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const [highlightIndex, setHighlightIndex] = useState(-1);

  // Filtered list
  const filtered = search
    ? locations.filter((loc) =>
        loc.toLowerCase().includes(search.toLowerCase())
      )
    : locations;

  // Close on outside click
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  // Keyboard navigation
  function handleKeyDown(e: React.KeyboardEvent) {
    if (!isOpen && e.key === "ArrowDown") {
      setIsOpen(true);
      return;
    }

    if (!isOpen) return;

    switch (e.key) {
      case "ArrowDown":
        e.preventDefault();
        setHighlightIndex((prev) => Math.min(prev + 1, filtered.length - 1));
        break;
      case "ArrowUp":
        e.preventDefault();
        setHighlightIndex((prev) => Math.max(prev - 1, 0));
        break;
      case "Enter":
        e.preventDefault();
        if (highlightIndex >= 0 && highlightIndex < filtered.length) {
          selectLocation(filtered[highlightIndex]);
        }
        break;
      case "Escape":
        setIsOpen(false);
        setHighlightIndex(-1);
        break;
    }
  }

  function selectLocation(loc: string) {
    onChange(loc);
    setSearch("");
    setIsOpen(false);
    setHighlightIndex(-1);
  }

  function handleInputChange(e: React.ChangeEvent<HTMLInputElement>) {
    setSearch(e.target.value);
    setHighlightIndex(-1);
    if (!isOpen) setIsOpen(true);
  }

  function handleFocus() {
    setIsOpen(true);
  }

  // Highlight matching text
  function renderHighlightedText(text: string) {
    if (!search) return text;
    const idx = text.toLowerCase().indexOf(search.toLowerCase());
    if (idx === -1) return text;
    return (
      <>
        {text.slice(0, idx)}
        <mark className={styles.highlight}>{text.slice(idx, idx + search.length)}</mark>
        {text.slice(idx + search.length)}
      </>
    );
  }

  return (
    <div className={styles.container} ref={containerRef}>
      <div className={styles.inputWrapper}>
        <span className={`material-symbols-outlined ${styles.icon}`}>
          location_on
        </span>
        <input
          ref={inputRef}
          type="text"
          className={`form-input form-input--with-icon ${styles.input}`}
          placeholder={value || placeholder}
          value={isOpen ? search : value}
          onChange={handleInputChange}
          onFocus={handleFocus}
          onKeyDown={handleKeyDown}
          aria-label="Location"
          aria-expanded={isOpen}
          aria-haspopup="listbox"
          role="combobox"
          autoComplete="off"
        />
        <span
          className={`material-symbols-outlined ${styles.chevron} ${isOpen ? styles.chevronOpen : ""}`}
        >
          expand_more
        </span>
      </div>

      {isOpen && (
        <ul className={styles.dropdown} role="listbox">
          {filtered.length === 0 ? (
            <li className={styles.noResults}>No locations found</li>
          ) : (
            filtered.slice(0, 200).map((loc, idx) => (
              <li
                key={loc}
                className={`${styles.option} ${idx === highlightIndex ? styles.optionHighlighted : ""}`}
                onClick={() => selectLocation(loc)}
                role="option"
                aria-selected={loc === value}
              >
                {renderHighlightedText(loc)}
              </li>
            ))
          )}
        </ul>
      )}
    </div>
  );
}
