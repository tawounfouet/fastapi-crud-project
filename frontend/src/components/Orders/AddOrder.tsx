import {
  Button,
  Field,
  Input,
  NumberInput,
  Textarea,
  VStack,
  useDisclosure,
} from "@chakra-ui/react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { type SubmitHandler, useForm } from "react-hook-form"
import { FiPlus } from "react-icons/fi"

import { type ApiError, DemoService, type OrderCreate } from "@/client"
import {
  DialogActionTrigger,
  DialogBody,
  DialogCloseTrigger,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogRoot,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

interface AddOrderProps {
  disabled?: boolean
}

interface OrderFormData {
  status: string
  notes: string
  product_id: string
  quantity: number
  unit_price: number
}

const AddOrder = ({ disabled }: AddOrderProps) => {
  const queryClient = useQueryClient()
  const { showSuccessToast } = useCustomToast()
  const { open, onOpen, onClose } = useDisclosure()

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<OrderFormData>({
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      status: "pending",
      notes: "",
      product_id: "",
      quantity: 1,
      unit_price: 0,
    },
  })

  const mutation = useMutation({
    mutationFn: (data: OrderCreate) =>
      DemoService.createOrder({ requestBody: data }),
    onSuccess: () => {
      showSuccessToast("Order created successfully!")
      reset()
      onClose()
    },
    onError: (err: ApiError) => {
      handleError(err)
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["orders"] })
    },
  })

  const onSubmit: SubmitHandler<OrderFormData> = (data) => {
    const orderData: OrderCreate = {
      status: data.status,
      notes: data.notes || null,
      order_items: [
        {
          product_id: data.product_id,
          quantity: data.quantity,
          unit_price: data.unit_price,
        },
      ],
    }
    mutation.mutate(orderData)
  }

  return (
    <>
      <DialogRoot
        open={open}
        onOpenChange={({ open }) => (open ? onOpen() : onClose())}
      >
        <DialogTrigger asChild>
          <Button variant="solid" size="sm" disabled={disabled}>
            <FiPlus />
            Add Order
          </Button>
        </DialogTrigger>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add Order</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <VStack gap={4}>
              <Field.Root required invalid={!!errors.status}>
                <Field.Label htmlFor="status">Status</Field.Label>
                <Input
                  id="status"
                  {...register("status", {
                    required: "Status is required.",
                  })}
                  placeholder="pending"
                />
                <Field.ErrorText>{errors.status?.message}</Field.ErrorText>
              </Field.Root>

              <Field.Root required invalid={!!errors.product_id}>
                <Field.Label htmlFor="product_id">Product ID</Field.Label>
                <Input
                  id="product_id"
                  {...register("product_id", {
                    required: "Product ID is required.",
                  })}
                  placeholder="Enter product ID"
                />
                <Field.ErrorText>{errors.product_id?.message}</Field.ErrorText>
              </Field.Root>

              <Field.Root required invalid={!!errors.quantity}>
                <Field.Label htmlFor="quantity">Quantity</Field.Label>
                <NumberInput.Root min={1}>
                  <NumberInput.Input
                    id="quantity"
                    {...register("quantity", {
                      required: "Quantity is required.",
                      min: {
                        value: 1,
                        message: "Quantity must be at least 1.",
                      },
                      valueAsNumber: true,
                    })}
                    placeholder="1"
                  />
                </NumberInput.Root>
                <Field.ErrorText>{errors.quantity?.message}</Field.ErrorText>
              </Field.Root>

              <Field.Root required invalid={!!errors.unit_price}>
                <Field.Label htmlFor="unit_price">Unit Price</Field.Label>
                <NumberInput.Root min={0.01}>
                  <NumberInput.Input
                    id="unit_price"
                    {...register("unit_price", {
                      required: "Unit price is required.",
                      min: {
                        value: 0.01,
                        message: "Unit price must be greater than 0.",
                      },
                      valueAsNumber: true,
                    })}
                    placeholder="0.00"
                  />
                </NumberInput.Root>
                <Field.ErrorText>{errors.unit_price?.message}</Field.ErrorText>
              </Field.Root>

              <Field.Root invalid={!!errors.notes}>
                <Field.Label htmlFor="notes">Notes</Field.Label>
                <Textarea
                  id="notes"
                  {...register("notes", {
                    maxLength: {
                      value: 1000,
                      message: "Notes must be less than 1000 characters.",
                    },
                  })}
                  placeholder="Order notes (optional)"
                />
                <Field.ErrorText>{errors.notes?.message}</Field.ErrorText>
              </Field.Root>
            </VStack>
          </DialogBody>
          <DialogFooter>
            <DialogActionTrigger asChild>
              <Button variant="outline">Cancel</Button>
            </DialogActionTrigger>
            <Button
              variant="solid"
              type="submit"
              loading={isSubmitting}
              onClick={handleSubmit(onSubmit)}
            >
              Add Order
            </Button>
          </DialogFooter>
          <DialogCloseTrigger />
        </DialogContent>
      </DialogRoot>
    </>
  )
}

export default AddOrder
