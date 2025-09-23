// src/App.jsx
import { useRef, useState } from "react";
import axios from "axios";
import Papa from "papaparse";
import * as XLSX from "xlsx";
import "./App.css";

export default function App() {
  const [file, setFile] = useState(null);
  const [instruction, setInstruction] = useState("");
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [preview, setPreview] = useState(null); // { columns: string[], rows: any[] }
  const fileInputRef = useRef(null);
  const [activeTab, setActiveTab] = useState("original"); // original | after

  const parseFileToPreview = async (f) => {
    const ext = (f.name.split(".").pop() || "").toLowerCase();
    const arrayBuffer = await f.arrayBuffer();
    if (ext === "csv") {
      const text = new TextDecoder().decode(arrayBuffer);
      const parsed = Papa.parse(text, { header: true, skipEmptyLines: true });
      const rows = Array.isArray(parsed.data) ? parsed.data.slice(0, 100) : [];
      const columns = rows.length ? Object.keys(rows[0]) : (parsed.meta?.fields || []);
      setPreview({ columns, rows });
    } else if (ext === "xls" || ext === "xlsx") {
      const wb = XLSX.read(arrayBuffer, { type: "array" });
      const sheetName = wb.SheetNames[0];
      const ws = wb.Sheets[sheetName];
      const json = XLSX.utils.sheet_to_json(ws, { defval: "" });
      const rows = json.slice(0, 100);
      const columns = rows.length ? Object.keys(rows[0]) : [];
      setPreview({ columns, rows });
    } else {
      setError("Unsupported file type. Use CSV/XLS/XLSX.");
    }
  };

  const onSubmit = async (e) => {
    e.preventDefault();
    setError("");
    if (!file) {
      setError("Please select a CSV/XLS/XLSX file.");
      return;
    }

    const payload = JSON.stringify({ instruction, columns: null });
    const form = new FormData();
    form.append("file", file);
    form.append("payload", payload);

    try {
      setLoading(true);
      const res = await axios.post("/api/transform", form, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setData(res.data);
      setActiveTab("after");
    } catch (err) {
      const msg = err?.response?.data?.detail || err?.message || "Request failed";
      setError(String(msg));
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  const onUploadClick = (e) => {
    e.preventDefault();
    fileInputRef.current?.click();
  };

  const onFileChange = async (e) => {
    setError("");
    const f = e.target.files?.[0] ?? null;
    setFile(f);
    setData(null);
    if (f) {
      try {
        await parseFileToPreview(f);
        setActiveTab("original");
      } catch (err) {
        setError(String(err?.message || err) || "Preview failed");
        setPreview(null);
      }
    }
  };

  const compileSafeRegex = (pattern) => {
    try {
      return new RegExp(pattern, "g");
    } catch {
      return null;
    }
  };

  const highlightMatches = (text, pattern) => {
    const value = String(text ?? "");
    const re = compileSafeRegex(pattern);
    if (!re) return value;
    const parts = [];
    let last = 0;
    let m;
    while ((m = re.exec(value)) !== null) {
      const start = m.index;
      const end = re.lastIndex;
      if (start > last) parts.push(value.slice(last, start));
      parts.push(<mark key={start} style={{ background: '#fde68a' }}>{value.slice(start, end)}</mark>);
      last = end;
      if (m[0].length === 0) re.lastIndex++;
    }
    if (last < value.length) parts.push(value.slice(last));
    return parts;
  };

  const downloadProcessedData = async (format = 'csv') => {
    if (!file || !instruction) {
      setError("Please upload a file and enter a command first.");
      return;
    }

    try {
      setLoading(true);
      const payload = JSON.stringify({ instruction, columns: null });
      const form = new FormData();
      form.append("file", file);
      form.append("payload", payload);
      form.append("format", format);

      const res = await axios.post("/api/download", form, {
        headers: { "Content-Type": "multipart/form-data" },
        responseType: 'blob'
      });

      // Create download link
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `processed_data.${format}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
    } catch (err) {
      const msg = err?.response?.data?.detail || err?.message || "Download failed";
      setError(String(msg));
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="container">
      <div className="header">
        <h1 className="title">Regex Pattern Match & Replace</h1>
      </div>

      <div className="card form-card">
        <form className="form" onSubmit={onSubmit}>
          <div className="input-section">
            <div className="input-group">
              <label className="input-label">input file</label>
              <div className="input-row">
                <button onClick={onUploadClick} type="button" className="btn btn-secondary">upload</button>
                <input ref={fileInputRef} style={{ display: "none" }} type="file" accept=".csv,.xls,.xlsx" onChange={onFileChange} />
                <span className="filename">{file ? file.name : "filename"}</span>
              </div>
            </div>

            <div className="input-group">
              <label className="input-label">command</label>
              <div className="input-row">
                <input
                  className="command-input"
                  value={instruction}
                  onChange={e=>setInstruction(e.target.value)}
                  placeholder="Enter your command here..."
                />
                <button type="submit" disabled={loading} className="btn btn-primary execute-btn">
                  {loading ? "Processing..." : "execute"}
                </button>
              </div>
            </div>
          </div>
        </form>
        {error && <p className="error">{error}</p>}
      </div>

      {(preview || data) && (
        <div className="card content-card">
          <div className="tabs">
            <button
              className={`tab ${activeTab === 'original' ? 'tab-active' : ''}`}
              onClick={() => setActiveTab('original')}
              type="button"
              disabled={!preview}
            >original</button>
            <button
              className={`tab ${activeTab === 'after' ? 'tab-active' : ''}`}
              onClick={() => setActiveTab('after')}
              type="button"
              disabled={!data}
            >after</button>
          </div>

          <div className="content-area">
            {activeTab === 'original' && preview && (
              <>
                <div className="table-wrap">
                  <table className="table">
                    <thead>
                      <tr>{preview.columns.map(c => <th key={c}>{c}</th>)}</tr>
                    </thead>
                    <tbody>
                      {preview.rows.map((r, i) => (
                        <tr key={i}>
                          {preview.columns.map(c => <td key={c}>{data?.regexUsed ? highlightMatches(r[c], data.regexUsed) : String(r[c] ?? "")}</td>)}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div className="meta">Showing first {preview.rows.length} rows.</div>
              </>
            )}

            {activeTab === 'after' && data && (
              <>
                <div className="meta"><b>Regex used:</b> {data.regexUsed}</div>
                <div className="meta"><b>Applied columns:</b> {data.columnsApplied.join(", ") || "(none)"}</div>
                <div className="download-section">
                  <button 
                    onClick={() => downloadProcessedData('csv')} 
                    disabled={loading}
                    className="btn btn-secondary download-btn"
                  >
                    Download CSV
                  </button>
                  <button 
                    onClick={() => downloadProcessedData('xlsx')} 
                    disabled={loading}
                    className="btn btn-secondary download-btn"
                  >
                    Download Excel
                  </button>
                </div>
                <div className="table-wrap">
                  <table className="table">
                    <thead>
                      <tr>{data.columns.map(c => <th key={c}>{c}</th>)}</tr>
                    </thead>
                    <tbody>
                      {data.rows.map((r, i) => (
                        <tr key={i}>
                          {data.columns.map(c => {
                            const before = data.rowsOriginal?.[i]?.[c];
                            const after = r[c];
                            const changed = String(before ?? "") !== String(after ?? "");
                            return (
                              <td key={c} style={changed ? { background: '#ecfeff' } : undefined}>
                                {String(after ?? "")}
                              </td>
                            );
                          })}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div className="meta">Showing first {data.rows.length} of {data.totalRows} rows.</div>
              </>
            )}
          </div>
        </div>
      )}
    </main>
  );
}
