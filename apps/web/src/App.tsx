import { Route, Routes } from "react-router-dom";

import { AdminRoute, ProtectedRoute } from "@/components/layout/ProtectedRoute";
import { AccountLayout } from "@/layouts/AccountLayout";
import { AdminLayout } from "@/layouts/AdminLayout";
import { MainLayout } from "@/layouts/MainLayout";
import { AIStylistPage } from "@/pages/AIStylistPage";
import { CartPage } from "@/pages/CartPage";
import { CheckoutPage } from "@/pages/CheckoutPage";
import { HomePage } from "@/pages/HomePage";
import { LoginPage } from "@/pages/LoginPage";
import { NotFoundPage } from "@/pages/NotFoundPage";
import { OrderSuccessPage } from "@/pages/OrderSuccessPage";
import { ProductDetailPage } from "@/pages/ProductDetailPage";
import { RegisterPage } from "@/pages/RegisterPage";
import { ShopPage } from "@/pages/ShopPage";
import { AccountAddressesPage } from "@/pages/account/AccountAddressesPage";
import { AccountOrdersPage } from "@/pages/account/AccountOrdersPage";
import { AccountOverviewPage } from "@/pages/account/AccountOverviewPage";
import { AccountProfilePage } from "@/pages/account/AccountProfilePage";
import { AccountStyleProfilePage } from "@/pages/account/AccountStyleProfilePage";
import { AccountWishlistPage } from "@/pages/account/AccountWishlistPage";
import { AdminCouponsPage } from "@/pages/admin/AdminCouponsPage";
import { AdminCustomersPage } from "@/pages/admin/AdminCustomersPage";
import { AdminOrdersPage } from "@/pages/admin/AdminOrdersPage";
import { AdminOverviewPage } from "@/pages/admin/AdminOverviewPage";
import { AdminProductsPage } from "@/pages/admin/AdminProductsPage";
import { AdminReviewsPage } from "@/pages/admin/AdminReviewsPage";

export default function App() {
  return (
    <Routes>
      <Route element={<MainLayout />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/shop" element={<ShopPage />} />
        <Route path="/shop/men" element={<ShopPage gender="men" />} />
        <Route path="/shop/women" element={<ShopPage gender="women" />} />
        <Route path="/products/:slug" element={<ProductDetailPage />} />
        <Route path="/ai-stylist" element={<AIStylistPage />} />
        <Route path="/cart" element={<CartPage />} />
        <Route
          path="/checkout"
          element={
            <ProtectedRoute>
              <CheckoutPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/order-success/:orderId"
          element={
            <ProtectedRoute>
              <OrderSuccessPage />
            </ProtectedRoute>
          }
        />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />

        <Route
          element={
            <ProtectedRoute>
              <AccountLayout />
            </ProtectedRoute>
          }
        >
          <Route path="/account" element={<AccountOverviewPage />} />
          <Route path="/account/orders" element={<AccountOrdersPage />} />
          <Route path="/account/orders/:orderId" element={<OrderSuccessPage />} />
          <Route path="/account/wishlist" element={<AccountWishlistPage />} />
          <Route path="/account/addresses" element={<AccountAddressesPage />} />
          <Route path="/account/style-profile" element={<AccountStyleProfilePage />} />
          <Route path="/account/profile" element={<AccountProfilePage />} />
        </Route>

        <Route path="*" element={<NotFoundPage />} />
      </Route>

      <Route
        element={
          <AdminRoute>
            <AdminLayout />
          </AdminRoute>
        }
      >
        <Route path="/admin" element={<AdminOverviewPage />} />
        <Route path="/admin/products" element={<AdminProductsPage />} />
        <Route path="/admin/orders" element={<AdminOrdersPage />} />
        <Route path="/admin/customers" element={<AdminCustomersPage />} />
        <Route path="/admin/coupons" element={<AdminCouponsPage />} />
        <Route path="/admin/reviews" element={<AdminReviewsPage />} />
      </Route>
    </Routes>
  );
}
