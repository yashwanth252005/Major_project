export default async function exportReportPdf(rootEl, scanId) {
  const [{ jsPDF }, { default: html2canvas }] = await Promise.all([
    import("jspdf"),
    import("html2canvas"),
  ]);

  const sections = rootEl.querySelectorAll("[data-pdf-section]");

  const pdf = new jsPDF({ orientation: "portrait", unit: "mm", format: "a4" });
  const marginX = 10;
  const top = 10;
  const contentW = 190;
  const pageBottom = 287; // last mm where content may start/end on a4 (297mm tall)
  const pageH = 277; // max rendered section height per page
  let currentY = top;
  let firstPage = true; // still on the initially-created page?

  for (const el of sections) {
    const canvas = await html2canvas(el, {
      scale: 2,
      backgroundColor: null,
      useCORS: true,
    });
    const h_mm = (contentW * canvas.height) / canvas.width;

    if (h_mm <= pageH) {
      // Fits on one page: start a new page only if it would overflow the current one.
      if (!firstPage && currentY + h_mm > pageBottom) {
        pdf.addPage();
        currentY = top;
      }
      pdf.addImage(canvas.toDataURL("image/png"), "PNG", marginX, currentY, contentW, h_mm);
      currentY += h_mm + 4;
      firstPage = false;
    } else {
      // Oversized section: slice it into page-height bands, each on a fresh page.
      const bandH_px = Math.max(1, Math.floor(canvas.width * (pageH / contentW)));
      let offsetY = 0;
      while (offsetY < canvas.height) {
        const thisBandH = Math.min(bandH_px, canvas.height - offsetY);
        const band = document.createElement("canvas");
        band.width = canvas.width;
        band.height = thisBandH;
        band.getContext("2d").drawImage(canvas, 0, -offsetY);

        if (!firstPage) pdf.addPage();
        currentY = top;
        const bandH_mm = (contentW * thisBandH) / canvas.width;
        pdf.addImage(band.toDataURL("image/png"), "PNG", marginX, currentY, contentW, bandH_mm);
        currentY += bandH_mm + 4;
        firstPage = false;
        offsetY += thisBandH;
      }
    }
  }

  pdf.save(`neuroscan-report-${scanId.slice(0, 8)}.pdf`);
}
