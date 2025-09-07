import type React from "react"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { forwardRef } from "react"

interface FormInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label: string
  required?: boolean
  error?: string
  variant?: "default" | "dineconnect"
}

export const FormInput = forwardRef<HTMLInputElement, FormInputProps>(
  ({ label, required, error, variant = "default", className, ...props }, ref) => {
    const baseClasses = "mt-1 block w-full shadow-sm sm:text-sm px-4 py-3"
    const variantClasses = {
      default:
        "rounded-lg border-gray-300 bg-white focus:border-[var(--primary-color)] focus:ring-[var(--primary-color)]",
      dineconnect: "rounded-full border-[#e5e7eb] bg-white focus:border-[#ea2a33] focus:ring-[#ea2a33]",
    }

    return (
      <div>
        <Label htmlFor={props.id} className="block text-sm font-medium">
          {label} {required && <span className="text-red-500">*</span>}
        </Label>
        <Input ref={ref} className={`${baseClasses} ${variantClasses[variant]} ${className || ""}`} {...props} />
        {error && <p className="mt-1 text-sm text-red-600">{error}</p>}
      </div>
    )
  },
)

FormInput.displayName = "FormInput"
