import { Button, Text } from "@chakra-ui/react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { FiTrash2 } from "react-icons/fi"

import { type ApiError, DemoService, type ProductPublic } from "@/client"
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

interface DeleteProductProps {
  product: ProductPublic
  disabled?: boolean
}

const DeleteProduct = ({ product, disabled }: DeleteProductProps) => {
  const queryClient = useQueryClient()
  const { showSuccessToast } = useCustomToast()

  const mutation = useMutation({
    mutationFn: () => DemoService.deleteProduct({ productId: product.id }),
    onSuccess: () => {
      showSuccessToast("Product deleted successfully!")
    },
    onError: (err: ApiError) => {
      handleError(err)
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["products"] })
    },
  })

  const handleDelete = () => {
    mutation.mutate()
  }

  return (
    <>
      <DialogRoot>
        <DialogTrigger asChild>
          <Button
            variant="outline"
            size="sm"
            disabled={disabled}
            colorScheme="red"
          >
            <FiTrash2 />
            Delete
          </Button>
        </DialogTrigger>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Product</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <Text>
              Are you sure you want to delete the product "{product.name}"? This
              action cannot be undone.
            </Text>
          </DialogBody>
          <DialogFooter>
            <DialogActionTrigger asChild>
              <Button variant="outline">Cancel</Button>
            </DialogActionTrigger>
            <Button
              variant="solid"
              colorScheme="red"
              loading={mutation.isPending}
              onClick={handleDelete}
            >
              Delete Product
            </Button>
          </DialogFooter>
          <DialogCloseTrigger />
        </DialogContent>
      </DialogRoot>
    </>
  )
}

export default DeleteProduct
