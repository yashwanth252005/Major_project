/**
 * Shared card primitive. Optional numbered chip (index) replaces the old
 * .panel-index heading style; `pdf` marks the card as an exportable PDF
 * section (exportPdf.js collects [data-pdf-section] inside the report root).
 */
export default function Card({
  as: Tag = "section",
  title,
  index,
  actions,
  pdf,
  id,
  className,
  children,
}) {
  const classes = ["card"];
  if (className) classes.push(className);

  return (
    <Tag
      id={id}
      className={classes.join(" ")}
      {...(pdf ? { "data-pdf-section": "" } : {})}
    >
      {(title || actions || index != null) && (
        <div className="card__header">
          <div className="card__heading">
            {index != null && <span className="card__index">{index}</span>}
            {title && <h2 className="card__title">{title}</h2>}
          </div>
          {actions && <div className="card__actions">{actions}</div>}
        </div>
      )}
      {children}
    </Tag>
  );
}
