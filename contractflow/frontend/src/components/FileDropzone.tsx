import { useCallback } from "react";
import { useDropzone, type Accept } from "react-dropzone";
import { cn } from "@/lib/utils";

interface FileDropzoneProps {
  onFileAccepted: (file: File) => void;
  accept?: Accept;
  maxSizeMB?: number;
  disabled?: boolean;
  className?: string;
}

export function FileDropzone({
  onFileAccepted,
  accept,
  maxSizeMB = 50,
  disabled,
  className,
}: FileDropzoneProps) {
  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      if (acceptedFiles.length > 0) onFileAccepted(acceptedFiles[0]);
    },
    [onFileAccepted],
  );

  const { getRootProps, getInputProps, isDragActive, isDragReject } =
    useDropzone({
      onDrop,
      accept,
      maxSize: maxSizeMB * 1024 * 1024,
      multiple: false,
      disabled,
    });

  return (
    <div
      {...getRootProps()}
      className={cn(
        "flex flex-col items-center justify-center rounded-lg border-2 border-dashed p-8 text-center transition-colors cursor-pointer",
        isDragActive && "border-primary bg-primary/5",
        isDragReject && "border-destructive bg-destructive/5",
        disabled && "opacity-50 cursor-not-allowed",
        !isDragActive &&
          !isDragReject &&
          "border-muted-foreground/25 hover:border-muted-foreground/50",
        className,
      )}
    >
      <input {...getInputProps()} />
      {isDragActive ? (
        <p className="text-sm text-muted-foreground">
          Drop the file here...
        </p>
      ) : (
        <>
          <p className="text-sm font-medium">
            Drag & drop a file here, or click to select
          </p>
          <p className="text-xs text-muted-foreground mt-1">
            Max size: {maxSizeMB}MB
          </p>
        </>
      )}
    </div>
  );
}
