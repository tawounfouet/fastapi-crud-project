import {
  Box,
  Container,
  Flex,
  Heading,
  SimpleGrid,
  Text,
  VStack,
} from "@chakra-ui/react"
import { useQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"

import { DemoService } from "@/client"

export const Route = createFileRoute("/_layout/dashboard")({
  component: Dashboard,
})

function Dashboard() {
  const { data, isLoading } = useQuery({
    queryFn: () => DemoService.getDashboardStats(),
    queryKey: ["dashboard-stats"],
  })

  if (isLoading) {
    return (
      <Container maxW="full" py={4}>
        <Text>Loading dashboard...</Text>
      </Container>
    )
  }

  return (
    <Container maxW="full" py={4}>
      <VStack gap={6} align="stretch">
        <Heading size="lg" textAlign={{ base: "center", md: "left" }}>
          Dashboard
        </Heading>

        {data && (
          <>
            <SimpleGrid columns={{ base: 1, md: 2 }} gap={6}>
              <Box p={6} borderWidth={1} borderRadius="md">
                <VStack align="start" gap={2}>
                  <Heading size="md">Products</Heading>
                  <Text>Total Products: {data.products.total_products}</Text>
                  <Text>Active Products: {data.products.active_products}</Text>
                  <Text>
                    Total Categories: {data.products.total_categories}
                  </Text>
                  <Text>
                    Low Stock Products: {data.products.low_stock_products}
                  </Text>
                </VStack>
              </Box>

              <Box p={6} borderWidth={1} borderRadius="md">
                <VStack align="start" gap={2}>
                  <Heading size="md">Orders</Heading>
                  <Text>Total Orders: {data.orders.total_orders}</Text>
                  <Text>Total Revenue: ${data.orders.total_revenue}</Text>
                  <Text>Completed Orders: {data.orders.completed_orders}</Text>
                  <Text>Pending Orders: {data.orders.pending_orders}</Text>
                </VStack>
              </Box>
            </SimpleGrid>

            {data.recent_orders && data.recent_orders.length > 0 && (
              <Box>
                <Heading size="md" mb={4}>
                  Recent Orders
                </Heading>
                <VStack gap={3} align="stretch">
                  {data.recent_orders.map((order) => (
                    <Flex
                      key={order.id}
                      p={4}
                      borderWidth={1}
                      borderRadius="md"
                      justify="space-between"
                      align="center"
                    >
                      <VStack align="start" gap={1}>
                        <Text fontWeight="bold">Order #{order.id}</Text>
                        <Text fontSize="sm">Status: {order.status}</Text>
                        <Text fontSize="sm">Total: ${order.total_amount}</Text>
                      </VStack>
                    </Flex>
                  ))}
                </VStack>
              </Box>
            )}
          </>
        )}
      </VStack>
    </Container>
  )
}
