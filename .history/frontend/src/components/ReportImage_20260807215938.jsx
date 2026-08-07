import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ZoomIn, X } from "lucide-react";

export default function ReportImage({
  title,
  base64,
  description,
}) {
  const [open, setOpen] = useState(false);

  return (
    <>
      <motion.div
        whileHover={{ y: -6 }}
        transition={{ duration: 0.25 }}
        className="surface-hover overflow-hidden rounded-3xl"
      >
        {/* Header */}

        <div className="flex items-center justify-between border-b border-white/10 px-5 py-4">

          <div>

            <h3 className="font-semibold">
              {title}
            </h3>

            {description && (
              <p className="mt-1 text-xs text-slate-400">
                {description}
              </p>
            )}

          </div>

        </div>

        {/* Image */}

        {base64 ? (

          <div
            onClick={() => setOpen(true)}
            className="group relative cursor-pointer overflow-hidden"
          >

            <img
              src={`data:image/png;base64,${base64}`}
              alt={title}
              className="h-72 w-full object-contain bg-[#0D1422] transition duration-500 group-hover:scale-105"
            />

            {/* Overlay */}

            <div className="absolute inset-0 flex items-center justify-center bg-black/0 transition group-hover:bg-black/35">

              <div className="rounded-full bg-white/10 p-3 opacity-0 backdrop-blur transition group-hover:opacity-100">

                <ZoomIn className="text-white" />

              </div>

            </div>

          </div>

        ) : (

          <div className="flex h-72 items-center justify-center bg-[#0D1422] text-slate-500">

            No Image Available

          </div>

        )}

      </motion.div>

      {/* Lightbox */}

      <AnimatePresence>

        {open && (

          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/90 p-8"
            onClick={() => setOpen(false)}
          >

            <button
              className="absolute right-6 top-6 rounded-full bg-white/10 p-3"
            >

              <X className="text-white" />

            </button>

            <motion.img
              initial={{ scale: .85 }}
              animate={{ scale: 1 }}
              exit={{ scale: .85 }}
              transition={{ duration: .25 }}
              src={`data:image/png;base64,${base64}`}
              alt={title}
              className="max-h-[90vh] max-w-[90vw] rounded-3xl shadow-2xl"
            />

          </motion.div>

        )}

      </AnimatePresence>

    </>
  );
}