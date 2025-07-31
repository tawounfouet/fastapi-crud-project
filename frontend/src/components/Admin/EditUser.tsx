import { useQueryClient } from "@tanstack/react-query"
import { Controller, type SubmitHandler, useForm } from "react-hook-form"

import {
  Button,
  DialogActionTrigger,
  DialogRoot,
  DialogTrigger,
  Flex,
  Input,
  Text,
  VStack,
} from "@chakra-ui/react"
import { useState } from "react"
import { FaExchangeAlt } from "react-icons/fa"

import { type UserPublicOutput, type UserUpdate, UsersService } from "@/client"
import useCustomToast from "@/hooks/useCustomToast"
import { emailPattern, handleError } from "@/utils"
import { toaster } from "@/components/ui/toaster"
import { Checkbox } from "../ui/checkbox"
import {
  DialogBody,
  DialogCloseTrigger,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "../ui/dialog"
import { Field } from "../ui/field"

interface EditUserProps {
  user: UserPublicOutput
}

interface UserUpdateForm extends UserUpdate {
  confirm_password?: string
  is_superuser?: boolean
}

const EditUser = ({ user }: EditUserProps) => {
  const [isOpen, setIsOpen] = useState(false)
  const queryClient = useQueryClient()
  const { showSuccessToast } = useCustomToast()
  const {
    control,
    register,
    handleSubmit,
    reset,
    getValues,
    formState: { errors, isSubmitting },
  } = useForm<UserUpdateForm>({
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: user,
  })

  const onSubmit: SubmitHandler<UserUpdateForm> = async (data) => {
    if (data.password === "") {
      data.password = undefined
    }
    
    // Filter out fields not accepted by UserUpdate schema
    const filteredData: UserUpdate = {
      email: data.email,
      first_name: data.first_name,
      last_name: data.last_name,
      password: data.password,
      is_active: data.is_active,
    }
    
    try {
      // First update the user with the allowed fields
      await UsersService.updateUserById({ userId: user.id, requestBody: filteredData })
      
      // Handle superuser promotion separately
      if (data.is_superuser && !user.is_superuser) {
        // Promote to superuser if checkbox is checked and user wasn't a superuser
        await UsersService.promoteUserToSuperuser({ userId: user.id })
      } else if (!data.is_superuser && user.is_superuser) {
        // Note: There's no demote endpoint in the API
        toaster.create({
          title: "Warning",
          description: "Cannot remove superuser privileges. This feature is not implemented in the API.",
          type: "warning",
        })
        return
      }
      
      showSuccessToast("User updated successfully.")
      reset()
      setIsOpen(false)
      // Force immediate cache invalidation
      queryClient.invalidateQueries({ queryKey: ["users"] })
      queryClient.invalidateQueries({ queryKey: ["currentUser"] })
      // Refetch data to ensure UI updates
      queryClient.refetchQueries({ queryKey: ["users"] })
    } catch (err: any) {
      handleError(err)
    }
  }

  return (
    <DialogRoot
      size={{ base: "xs", md: "md" }}
      placement="center"
      open={isOpen}
      onOpenChange={({ open }) => setIsOpen(open)}
    >
      <DialogTrigger asChild>
        <Button variant="ghost" size="sm">
          <FaExchangeAlt fontSize="16px" />
          Edit User
        </Button>
      </DialogTrigger>
      <DialogContent>
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogHeader>
            <DialogTitle>Edit User</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <Text mb={4}>Update the user details below.</Text>
            <VStack gap={4}>
              <Field
                required
                invalid={!!errors.email}
                errorText={errors.email?.message}
                label="Email"
              >
                <Input
                  id="email"
                  {...register("email", {
                    required: "Email is required",
                    pattern: emailPattern,
                  })}
                  placeholder="Email"
                  type="email"
                />
              </Field>

              <Field
                invalid={!!errors.first_name}
                errorText={errors.first_name?.message}
                label="First Name"
              >
                <Input
                  id="first_name"
                  {...register("first_name")}
                  placeholder="First name"
                  type="text"
                />
              </Field>

              <Field
                invalid={!!errors.last_name}
                errorText={errors.last_name?.message}
                label="Last Name"
              >
                <Input
                  id="last_name"
                  {...register("last_name")}
                  placeholder="Last name"
                  type="text"
                />
              </Field>

              <Field
                invalid={!!errors.password}
                errorText={errors.password?.message}
                label="Set Password"
              >
                <Input
                  id="password"
                  {...register("password", {
                    minLength: {
                      value: 8,
                      message: "Password must be at least 8 characters",
                    },
                  })}
                  placeholder="Password"
                  type="password"
                />
              </Field>

              <Field
                invalid={!!errors.confirm_password}
                errorText={errors.confirm_password?.message}
                label="Confirm Password"
              >
                <Input
                  id="confirm_password"
                  {...register("confirm_password", {
                    validate: (value) =>
                      value === getValues().password ||
                      "The passwords do not match",
                  })}
                  placeholder="Password"
                  type="password"
                />
              </Field>
            </VStack>

            <Flex mt={4} direction="column" gap={4}>
              <Controller
                control={control}
                name="is_superuser"
                render={({ field }) => (
                  <Field disabled={field.disabled} colorPalette="teal">
                    <Checkbox
                      checked={!!field.value}
                      onCheckedChange={({ checked }) => field.onChange(!!checked)}
                    >
                      Is superuser?
                    </Checkbox>
                  </Field>
                )}
              />
              <Controller
                control={control}
                name="is_active"
                render={({ field }) => (
                  <Field disabled={field.disabled} colorPalette="teal">
                    <Checkbox
                      checked={!!field.value}
                      onCheckedChange={({ checked }) => field.onChange(!!checked)}
                    >
                      Is active?
                    </Checkbox>
                  </Field>
                )}
              />
            </Flex>
          </DialogBody>

          <DialogFooter gap={2}>
            <DialogActionTrigger asChild>
              <Button
                variant="subtle"
                colorPalette="gray"
                disabled={isSubmitting}
              >
                Cancel
              </Button>
            </DialogActionTrigger>
            <Button variant="solid" type="submit" loading={isSubmitting}>
              Save
            </Button>
          </DialogFooter>
          <DialogCloseTrigger />
        </form>
      </DialogContent>
    </DialogRoot>
  )
}

export default EditUser
