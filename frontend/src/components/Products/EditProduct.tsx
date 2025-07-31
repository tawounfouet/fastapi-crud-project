import {
  Button,
  Field,
  Input,
  NumberInput,
  Switch,
  Textarea,
  VStack,
  useDisclosure,
} from "@chakra-ui/react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { type SubmitHandler, useForm } from "react-hook-form"
import { FiEdit } from "react-icons/fi"

import {
  type ApiError,
  DemoService,
  type ProductPublic,
  type ProductUpdate,
} from "@/client"
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

interface EditProductProps {
  product: ProductPublic
  disabled?: boolean
}

const EditProduct = ({ product, disabled }: EditProductProps) => {
  const queryClient = useQueryClient()
  const { showSuccessToast } = useCustomToast()
  const { open, onOpen, onClose } = useDisclosure()

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<ProductUpdate>({
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      name: product.name,
      description: product.description,
      price: product.price,
      category: product.category,
      stock_quantity: product.stock_quantity,
      is_active: product.is_active,
    },
  })

  const mutation = useMutation({
    mutationFn: (data: ProductUpdate) =>
      DemoService.updateProduct({ productId: product.id, requestBody: data }),
    onSuccess: () => {
      showSuccessToast("Product updated successfully!")
      onClose()
    },
    onError: (err: ApiError) => {
      handleError(err)
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["products"] })
    },
  })

  const onSubmit: SubmitHandler<ProductUpdate> = (data) => {
    mutation.mutate(data)
  }

  const onCancel = () => {
    reset()
    onClose()
  }

  return (
    <>
      <DialogRoot
        open={open}
        onOpenChange={({ open }) => (open ? onOpen() : onClose())}
      >
        <DialogTrigger asChild>
          <Button variant="outline" size="sm" disabled={disabled}>
            <FiEdit />
            Edit
          </Button>
        </DialogTrigger>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit Product</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <VStack gap={4}>
              <Field.Root required invalid={!!errors.name}>
                <Field.Label htmlFor="name">Name</Field.Label>
                <Input
                  id="name"
                  {...register("name", {
                    required: "Name is required.",
                    maxLength: {
                      value: 255,
                      message: "Name must be less than 255 characters.",
                    },
                  })}
                  placeholder="Product name"
                />
                <Field.ErrorText>{errors.name?.message}</Field.ErrorText>
              </Field.Root>

              <Field.Root invalid={!!errors.description}>
                <Field.Label htmlFor="description">Description</Field.Label>
                <Textarea
                  id="description"
                  {...register("description", {
                    maxLength: {
                      value: 1000,
                      message: "Description must be less than 1000 characters.",
                    },
                  })}
                  placeholder="Product description"
                />
                <Field.ErrorText>{errors.description?.message}</Field.ErrorText>
              </Field.Root>

              <Field.Root required invalid={!!errors.price}>
                <Field.Label htmlFor="price">Price</Field.Label>
                <NumberInput.Root min={0.01}>
                  <NumberInput.Input
                    id="price"
                    {...register("price", {
                      required: "Price is required.",
                      min: {
                        value: 0.01,
                        message: "Price must be greater than 0.",
                      },
                      valueAsNumber: true,
                    })}
                    placeholder="0.00"
                  />
                </NumberInput.Root>
                <Field.ErrorText>{errors.price?.message}</Field.ErrorText>
              </Field.Root>

              <Field.Root required invalid={!!errors.category}>
                <Field.Label htmlFor="category">Category</Field.Label>
                <Input
                  id="category"
                  {...register("category", {
                    required: "Category is required.",
                    maxLength: {
                      value: 100,
                      message: "Category must be less than 100 characters.",
                    },
                  })}
                  placeholder="Product category"
                />
                <Field.ErrorText>{errors.category?.message}</Field.ErrorText>
              </Field.Root>

              <Field.Root required invalid={!!errors.stock_quantity}>
                <Field.Label htmlFor="stock_quantity">
                  Stock Quantity
                </Field.Label>
                <NumberInput.Root min={0}>
                  <NumberInput.Input
                    id="stock_quantity"
                    {...register("stock_quantity", {
                      required: "Stock quantity is required.",
                      min: {
                        value: 0,
                        message: "Stock quantity must be non-negative.",
                      },
                      valueAsNumber: true,
                    })}
                    placeholder="0"
                  />
                </NumberInput.Root>
                <Field.ErrorText>
                  {errors.stock_quantity?.message}
                </Field.ErrorText>
              </Field.Root>

              <Field.Root>
                <Field.Label htmlFor="is_active">Active</Field.Label>
                <Switch.Root {...register("is_active")}>
                  <Switch.Control>
                    <Switch.Thumb />
                  </Switch.Control>
                </Switch.Root>
              </Field.Root>
            </VStack>
          </DialogBody>
          <DialogFooter>
            <DialogActionTrigger asChild>
              <Button variant="outline" onClick={onCancel}>
                Cancel
              </Button>
            </DialogActionTrigger>
            <Button
              variant="solid"
              type="submit"
              loading={isSubmitting}
              onClick={handleSubmit(onSubmit)}
            >
              Update Product
            </Button>
          </DialogFooter>
          <DialogCloseTrigger />
        </DialogContent>
      </DialogRoot>
    </>
  )
}

export default EditProduct
